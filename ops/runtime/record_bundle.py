"""Offline unverified control-record preparation; never publishes or attests host.

Input is a private candidate bundle, not proof or authority. Hashes identify the
exact canonical record bytes a separately authorized publisher would review.
"""
import base64
import hashlib
import json
from control import unique_fields
from guard import require,validate_expected
import operator_inspect
import process_probe
import schema_reconciliation

MAX_BUNDLE=3145728
FILENAMES={'expected.json','database-process.json','operator-connection.json','schema-reconciliation.json'}


def prepare_records(data):
    require(type(data) is bytes and 0<len(data)<=MAX_BUNDLE)
    value=json.loads(data.decode('utf8'),object_pairs_hook=unique_fields)
    require(type(value) is dict and set(value)=={'schema_version','evidence_class','records','artifact_base64'})
    require(type(value['schema_version']) is int and value['schema_version']==1
            and value['evidence_class']=='unverified-candidate')
    records=value['records']
    require(type(records) is dict and set(records)==FILENAMES)
    payloads={name:json.dumps(record,sort_keys=True,separators=(',',':'),ensure_ascii=True,
                           allow_nan=False).encode('ascii')+b'\n' for name,record in records.items()}
    require(all(len(payload)<=32768 for payload in payloads.values()))
    expected=validate_expected(records['expected.json'])
    process=process_probe.validate_record(records['database-process.json'])
    connection=operator_inspect.validate_connection(records['operator-connection.json'])
    authorization=schema_reconciliation.validate_authorization(records['schema-reconciliation.json'])
    require(process['startup']==expected)
    operator_inspect.validate_bindings(connection,process,authorization)
    encoded=value['artifact_base64']
    require(type(encoded) is str and len(encoded)<=2796204)
    artifact=base64.b64decode(encoded,validate=True)
    schema_reconciliation.validate_artifact(artifact,authorization)
    report={'schema_version':1,'status':'candidate_validated','evidence_class':'unverified-candidate',
        'publication_authorized':False,'retry_authorized':False,'reopening_authorized':False,
        'bundle_sha256':hashlib.sha256(data).hexdigest(),
        'record_sha256':{name:hashlib.sha256(payloads[name]).hexdigest() for name in sorted(FILENAMES)}}
    return payloads,report
