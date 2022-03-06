import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from core.monitoring.data_collector import Online_Collector
from azureml.core.authentication import ServicePrincipalAuthentication
import time
import pandas as pd
from azureml.core import Workspace
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.helpers import dataframe_from_result_table
def init_data(tenant_id, client_id,client_secret,cluster_uri,database_name,all_data_table_name, datastore_name, file_dataset_name, base_path):

    KCSB_DATA = KustoConnectionStringBuilder.with_aad_application_key_authentication(cluster_uri, client_id, client_secret, tenant_id)
    client = KustoClient(KCSB_DATA)
    query= f"""
    {all_data_table_name}|limit 1
    """
    try:
        response = client.execute(database_name, query)
    except:
        print("tables not created, go on creating tables")
        #setup all_examples_table
        sample_data_all_table = pd.DataFrame({"file_path":['azureml://datastores/mltraining/paths/tmp/tmpev5bi0hz'],"label":['livingroom']})
        collector = Online_Collector(tenant_id, client_id,client_secret,cluster_uri,database_name,all_data_table_name, sample_data_all_table)
        dataset = ws.datasets[file_dataset_name]
        paths = dataset.to_path()
        file_paths=[]
        labels =[]
        for path in paths:
            file_paths.append(f'azureml://datastores/{datastore_name}/paths/{base_path+path}')
            labels.append(path.split("/")[-2])
        all_data = pd.DataFrame({"file_path":file_paths, "label":labels})
        t=0
        while(t<10):
            try:
                collector.stream_collect(all_data)
                break
            except:
                #tables are not ready, retry
                time.sleep(20)
            t+=1



# run script
if __name__ == "__main__":
    f=open("src/active_learning_cv/simulation/params.json")

    secret = os.environ.get("SP_SECRET")
    client_id = os.environ.get("SP_ID")
    tenant_id = params["tenant_id"]
    sp = ServicePrincipalAuthentication(tenant_id=tenant_id, service_principal_id=client_id,service_principal_password=secret)
    ws = Workspace.from_config(path="src/active_learning_cv/core", auth=sp)    
    kv=ws.get_default_keyvault()
    params =json.load(f)
    database_name=params["database_name"]
    cluster_uri = params["cluster_uri"]
    base_path =params["base_path"]
    all_data_dataset=params["all_data_dataset"]
    datastore_name =params["datastore_name"]
    all_data_table_name= params["all_data_table_name"]
    init_data(tenant_id, client_id,secret,cluster_uri,database_name,all_data_table_name, datastore_name, all_data_dataset, base_path)
