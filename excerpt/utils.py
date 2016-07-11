import os
import yaml
import boto3
from copy import deepcopy
from subprocess import Popen
from subprocess import check_call
from subprocess import CalledProcessError


class MySQLDump:

    def __init__(self, host=None, port=None, username=None, password=None, db=None, **kwargs):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._db = db
        self._head_args = []
        self._tail_args = []
        self._s3_target = []

    def _base_cmd(self):
        return [
            'mysqldump',
            '-u', self._username,
            '--password='+self._password,
            '-h', self._host,
            '--single-transaction',
            self._db,
        ]

    @property
    def cmd(self):
        return self._base_cmd() + self._head_args + self._tail_args

    def _copy_and_extend(self, target, cmd):
        new_dump = deepcopy(self)
        _target = "_"+target
        new_attr = getattr(new_dump, _target) + cmd
        setattr(new_dump, _target, new_attr)
        return new_dump

    def table(self, tbl):
        return self._copy_and_extend("tail_args", [tbl])

    def where(self, clause=None):
        if clause:
            return self._copy_and_extend("tail_args", ["--where", clause])
        else:
            return self

    def to(self, target=None, **kwargs):
        if target:
            return self._copy_and_extend("head_args", ["-r", target])
        else:
            if kwargs.get('s3'):
                bucket, key = kwargs.pop('s3')
                return self._copy_and_extend("s3_target", [(bucket, key)])

    def run(self):
        if self._s3_target:
            client = boto3.client('s3')
            for bucket, key in self._s3_target:
                s3tempfile ="{}-{}".format(bucket,key)
                s3dump = self._copy_and_extend("head_args", ["-r", s3tempfile])
                print(s3dump.cmd)
                for c in s3dump.cmd:
                    print type(c)
                if check_call(s3dump.cmd) == 0:
                    client.upload_file(s3tempfile, bucket, key)
                    os.remove(s3tempfile)
        else:
            check_call(self.cmd)

    @classmethod
    def from_dict(cls, dump_spec):
        """
        {
            "host": "<host>",
            "port": "<port>",
            "username": "<username>",
            "password": "<password>",
            "db": "<db>",
            "tables": [
                {"name": "<table_name>", "where": "<where_clause>"},
            ]
        }
        """
        dump = cls(
            host=dump_spec['host'],
            port=dump_spec['port'],
            username=dump_spec['username'],
            password=dump_spec['password'],
            db=dump_spec['db'],
        )
        for tbl in dump_spec.get('tables'):
            table_name, where_clause = tbl.get('name'), tbl.get('where')
            dump = dump.table(table_name).where(where_clause)
        return dump

    @classmethod
    def from_yaml(cls, yaml_spec):
        return cls.from_dict(yaml.load(yaml_spec))

    def _to_s3(self, bucket=None, filename=None):
        try:
            client = boto3.client('s3')
            self.to(filename)
            client.upload_file(filename, bucket, filename)
        except Exception as e:
            raise e
        finally:
            os.remove(filename)


def main():
    dump = MySQLDump(
        host="",
        port=,
        username="",
        password="",
        db="",
    ) # TODO - these were hardcoded to dose specifcs
    dump = dump.table("sources") \
               .where("id=1") \
               .table("source_metrics") \
               #.to("myfile.sql")
    dump.run()
