#!/usr/bin/env python3
# coding=UTF-8

# copiar o script para /usr/lib/zabbix/externalscripts/

try:
    import requests             # https://requests.readthedocs.io/en/master/
    import urllib3
    import xmltodict
    import json
except ImportError as error:
    print(f'[{error}] Instate o pacote "{error.name}" com o comando "pip3 install {error.name}"\n'
          f'[{error}] Install "{error.name}" package with "pip3 install {error.name} command"\n'
          f'ERROR: import error')

    exit()

import requests
import urllib3
import xmltodict
import json
import sys
import re
from time import sleep


def request_paloalto_api(api_url, params, seconds, jobid='request'):
    try:
        urllib3.disable_warnings()
        request = requests.get(api_url, params=params, timeout=seconds, verify=False)
        return request
    except Exception as err:
        print(f'jobid {jobid} | A conexão com a API não foi estabelecida. Causa: [{err}]\n'
              f'jobid {jobid} | The connection has not been established.  Cause: [{err}]\n'
              f'ERROR: error trying to run job-id {jobid}')
        exit()


def verifica_parametros():
    if len(sys.argv) < 2:
        print(f'Informe os argumentos necessários : <reportname> <report-type:custom|dynamic> <url> '
              f'<timeout> <wait_time> <apikey> <format:xml|json>\n'
              f'Enter the required arguments      : <reportname> <report-type:custom|dynamic> <url> '
              f'<timeout> <wait_time> <apikey> <format:xml|json>\n'
              f'ERROR: general argument error')
        exit()
    else:
        try:
            timeout_received    = int(sys.argv[4])
            wait_time_received  = float(sys.argv[5])
        except ValueError as err:
            print(f'Erro com os parametros timeout ou wait-time. A variável timeout deve ser do tipo "int" e '
                  f'wait-time deve ser do tipo "int" ou "float"\n'
                  f'Valores recebidos: timeout_received={sys.argv[4]} ; wait_time_received={sys.argv[5]}\n'
                  f'ERROR: argument error (incorrect data type for timeout or delay)')
            exit()
        reporttype_received     = str(sys.argv[2]).lower()
        output_format_received  = str(sys.argv[7]).lower()
        reporttype_expected     = ['custom', 'dynamic']
        outputformat_expeted    = ['xml', 'json']
        if (reporttype_received not in reporttype_expected) or (output_format_received not in outputformat_expeted):
            print(f'Parametros incorretos: O tipo do relatorio deve ser {reporttype_expected} e formato '
                  f'de saída deve ser {outputformat_expeted}\n'
                  f'ERROR: argument error (incorrect report type or output format)')
            exit()
        else:
            pass


verifica_parametros()

reportname    = str(sys.argv[1])            # Nome do relarório personalizado
reporttype    = str(sys.argv[2])            # Tipo do relatório a ser gerado: custom ou synamic
url           = str(sys.argv[3])            # URL da API
timeout       = int(sys.argv[4])            # Timeout das consultas a API
wait_time     = float(sys.argv[5])          # Tempo de espera para que o relatório personalizado/dinâmico fique pronto
api_key       = str(sys.argv[6])            # Chave do usuário para acesso à API
output_format = str(sys.argv[7]).lower()    # Formato de saída do relatório: xml ou json

payload = {"type": 'report', "async": 'yes', "reporttype": reporttype, "reportname": reportname, "key": api_key}

jobid_request = request_paloalto_api(url, payload, timeout)
payload.clear()

if jobid_request.status_code != 200:
    print(f'HTTP Status code {jobid_request.status_code} - {jobid_request.reason}\n{jobid_request.text}\n'
          f'ERROR: request error to jobid request (status code={jobid_request.status_code})')
    exit()
elif 'application/xml' not in jobid_request.headers['Content-Type']:
    print(f"{url} repondeu com código {jobid_request.status_code}, porém tipo de conteúdo esperado era "
          f"'application/xml' e foi retornado '{jobid_request.headers['Content-Type']}'\n"
          f"ERROR: request error (incorret content-type)")
    exit()
else:
    job_id = re.findall('<job>(\d+)<\/job>', jobid_request.text)[0]
    sleep(wait_time)        # Aguardar um tempo para que o relatório seja produzido pelo firewall

    payload = {"type": 'report', "action": 'get', "job-id": job_id, "key": api_key}
    custom_report_request = request_paloalto_api(url, payload, timeout, job_id)
    if custom_report_request.status_code != 200:
        print(f'HTTP Status code {jobid_request.status_code} - {jobid_request.reason}\n{jobid_request.text}\n'
              f'ERROR: request error to custom report request (status code={custom_report_request.status_code})')
        exit()
    else:
        if output_format == 'json':
            my_dict = xmltodict.parse(custom_report_request.text)
            json_data = json.dumps(my_dict)
            print(json_data)                        # Saída em JSON
        else:
            print(custom_report_request.text)       # Saída XML
