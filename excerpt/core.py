import os
import time
import glob
import logging
import contextlib
import shutil
import tempfile
import boto3
from utils import MySQLDump
from subprocess import check_output
from subprocess import check_call
from subprocess import CalledProcessError

log = logging.getLogger(__name__)

MYSQL_REGISTRY_IMAGE = "" # TODO - these were hardcoded to dose specifcs
MYSQL_ROOT_PASSWORD="" # TODO - these were hardcoded to dose specifcs
DEFAULT_BUCKET = "" # TODO - these were hardcoded to dose specifcs


@contextlib.contextmanager
def cd(newdir, cleanup=lambda: True):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)
        cleanup()

@contextlib.contextmanager
def tempdir():
    dirpath = tempfile.mkdtemp()
    def cleanup():
        shutil.rmtree(dirpath)
    with cd(dirpath, cleanup):
        yield dirpath

def bucket_name(target_key):
    return "{}.{}".format(DEFAULT_BUCKET, target_key)

def create_extract(target_key, dump_spec):
    if not target_key:
        raise Exception("Must provide a target_key.")
    dump = MySQLDump(**dump_spec)
    with tempdir() as dir_path:
        log.debug("Creating temporary directory at {}".format(dir_path))

        log.debug("Iterating through tables...")
        for tbl in dump_spec['tables']:
            log.debug("    tbl={}".format(tbl))
            dest = tbl.get('name')+"_"+str(int(time.time()))+".sql"
            tbl_dump = dump.table(tbl.get('name')).where(tbl.get('where')).to(dest)
            tbl_dump.run()
            log.debug("Saving to destination -> {}".format(dest))

        # Now join all the files together
        all_files = glob.glob("*.sql")
        log.debug("all-files = {}".format(all_files))
        dumpfile_path = "datadump.sql"
        with open(dumpfile_path, "wb") as dumpfile:
            for ith_file in all_files:
                log.debug(ith_file)
                if ith_file != dumpfile:
                    with open(ith_file, 'rb') as f:
                        shutil.copyfileobj(f, dumpfile)

        fname = "{}.sql".format(int(time.time()))
        s3target = "s3://{}/{}".format(bucket_name(target_key), fname)
        log.info("Saving extract to {}".format(s3target))
        client = boto3.client('s3')
        # Note: creating a bucket is idempotent
        client.create_bucket(Bucket=bucket_name(target_key))
        client.upload_file(dumpfile_path,
                           bucket_name(target_key),
                           fname)
        return s3target

def load_cmd(s3target, env_vars):
    """Generate the a command that will run the container with the data extract.
    """
    cmd = ["docker", "run"]
    for key, val in env_vars:
        cmd += ["-e", "{}={}".format(key,val)]
    cmd += ['-e', 'MYSQL_ROOT_PASSWORD={}'.format(MYSQL_ROOT_PASSWORD)]
    cmd += ['-e', 'MYSQL_DATABASE=']  #TODO - this was hardcoded
    cmd += ['-e', 'INIT_WITH_S3_FILE={}'.format(s3target)]
    cmd += ['-d']  # Run in daemon-mode
    cmd += [MYSQL_REGISTRY_IMAGE]
    return cmd

def connect_cmd(container_id):
    return ["docker", "run", "-it", "--link",
           "{}:mysql".format(container_id),
           "--rm", MYSQL_REGISTRY_IMAGE,
           "sh", "-c",
           "exec mysql -h\"$MYSQL_PORT_3306_TCP_ADDR\" -P\"$MYSQL_PORT_3306_TCP_PORT\" -uroot -p\"$MYSQL_ENV_MYSQL_ROOT_PASSWORD\"",
    ]

def is_up(container_id):
    cmd = connect_cmd(container_id)
    cmd[-1] += "live_analytics -e \"select 1;\""
    try:
        print(check_output(cmd))
        return True
    except CalledProcessError as e:
        print(e.output)
        return False

def init_container(target_key, dump_spec, aws_config, wait_for_start=False):
    # Create the extract and upload to S3
    s3key = create_extract(target_key, dump_spec)
    cmd = load_cmd(s3key, aws_config.items())
    out_cmd = connect_cmd("`docker ps -q -l`")
    print(":::: Run the following command to start the mysql db with the extract you just created ::::")
    print("================================================================")
    print(" ".join(cmd))
    print("================================================================")
    print(":::: Run the following command to connect via the cli ::::")
    print("================================================================")
    print(" ".join(out_cmd[:-1]) + " '{}'".format(out_cmd[-1]))
    print("================================================================")


if __name__ == '__main__':
    main()
