#encode UTF-8
import slate3k as slate
import re
import numpy as np
import pandas as pd
import datetime
import os
import re

import warnings
warnings.simplefilter('ignore')

###Função que retorna um único DataFrame com dados de todos os negócios a partir de uma pasta com Notas de Corretagens em "pdf".
def extrair_textos_notas():
    df = pd.DataFrame()
    arquivos = os.listdir('Notas')
    for nota in arquivos:
        print(nota)
        with open('./Notas/' + nota,'rb') as f:
            extracted_text = slate.PDF(f)
        string = extracted_text[0]
        dict = {'nota' : nota, 'txt' : string }
        try:
            df = df.append(dict, ignore_index=True)
        except:
            print(f'Houve um erro com a nota {nota}')
    return(df)

###Função que cria dataframe com resumos das notas de corretagem.
def criar_df_resumos(df):
    
    df_notas = pd.DataFrame()

    for i in range(df.shape[0]):
        lst = df.txt[i].split('\n\n')
        dados = {'Nota' : df.nota[i].split('.')[0][8:], \
                'Data' : lst[lst.index('Data Pregão') + 1],\
                'Debentures' : lst[lst.index('Debêntures') + 1], \
                'Vendas_vista' : lst[lst.index('Vendas à vista') + 1], \
                'Compras_vista' : lst[lst.index('Compras à vista') + 1], \
                'Opcoes_compras' : lst[lst.index('Opções - Compras') + 1], \
                'Opcoes_vendas' : lst[lst.index('Opções - Vendas') + 1], \
                'Operacoes_termo' : lst[lst.index('Operações a Termo') + 1], \
                'Titulos_publicos' : lst[lst.index('Valor das Operações com Títulos Públicos (V. Nom.)') + 1], \
                'Total_operacoes' : lst[lst.index('Valor das Operações\nValor das Operações') + 1].split('\n')[0], \
                'Taxa_Liquidacao' : lst[lst.index('Taxa de Liquidação') + 1], \
                'Taxa_Registro' : lst[lst.index('Taxa de Registro') + 1], \
                'Total_clearing' : lst[lst.index('Total Clearing (CBLC)\nTotal Clearing (CBLC)') + 1].split('\n')[0], \
                'Taxa_TermoOpcoes' : lst[lst.index('Taxa de Termo / Opções') + 1], \
                'Taxa_ANA' : lst[lst.index('Taxa A.N.A.') + 1], \
                'Emolumentos' : lst[lst.index('Emolumentos') + 1], \
                'Total_bolsa' : lst[lst.index('Total Bolsa\nTotal Bolsa') + 1].split('\n')[0], \
                'Corretagem' : lst[lst.index('Corretagem') + 1], \
                'Total_Corretagem_Despesas' : lst[lst.index('Total Corretagem/Despesas\nTotal Corretagem/Despesas') + 1].split('\n')[0] \
                }
        #print(dados)
        df_tmp = pd.DataFrame(dados, index=['Nota'])
        df_notas = df_notas.append(df_tmp, ignore_index=True)

    df_notas['Data'] = pd.to_datetime(df_notas['Data'], format = '%d/%m/%Y')
    df_notas.iloc[:,2:] = df_notas.iloc[:,2:].apply(lambda x: x.str.replace(".", "").str.replace(",",".")).apply(pd.to_numeric)
    df_notas.head()

    return df_notas

###Função que cria dataframe com negocios das notas de corretagem.
def criar_df_negocios(df):

    df_negocio = pd.DataFrame()

    for j in range(df.shape[0]):

        lst = df.txt[j].split('\n\n')
        nota = df.nota[j].split('.')[0][8:]
        data_negocio = lst[lst.index('Data Pregão') + 1]
        pos_inicial = lst.index('Valor/Ajuste D/CD/C\nValor/Ajuste') + 1
        pos_final = lst.index('Resumo dos Negócios\nResumo dos Negócios')
        tamanho_lista = len(lst[pos_inicial: pos_final])
        tamanho_colunas = 9
        matrix = []
        coluna = 0
        tmp_lst = []
        tmp_lst.append(nota)
        tmp_lst.append(data_negocio)

        lst = lst[pos_inicial: pos_final]
        for i in range(len(lst)):      
            if coluna == 4:
                regex = re.compile('[#DFBCAHXPYLYI]')
                if regex.search(lst[i]) == None:
                    valor = 'NaN'
                    tmp_lst.append(valor)
                    coluna += 1
                    tmp_lst.append(lst[i])
                    coluna += 1
                else:
                    valor = lst[i]
                    tmp_lst.append(lst[i])
                    coluna += 1
            else:
                valor = lst[i]
                tmp_lst.append(valor)
                coluna +=1
            
            if coluna == tamanho_colunas: 
                matrix.append(tmp_lst)
                coluna = 0
                tmp_lst = []
                tmp_lst.append(nota)
                tmp_lst.append(data_negocio)

        df_tmp = pd.DataFrame(matrix, columns = ['Nota','Data','Mercado', 'C/V', 'Tipo_mercado', 'Titulo', 'Obs', 'Qtde', 'Preco_Ajuste', 'Valor_ajuste', 'D/C'])
        df_negocio = df_negocio.append(df_tmp, ignore_index= True)
        df_negocio['Data'] = pd.to_datetime(df_negocio['Data'], format = '%d/%m/%Y')
        df_negocio.iloc[:,7:10] = df_negocio.iloc[:,7:10].apply(lambda x: x.str.replace(".", "").str.replace(",",".")).apply(pd.to_numeric)

    df_negocio

###Função que faz o join entre os dataframes de negocios e resumos para calcular o custo ponderado de cada negocio.
def inclui_custo_negocio(df_resumo,df_negocio):

    df_teste = df_negocio.pivot_table(values=['Valor_ajuste'], index=['Nota','Titulo'], columns = ['C/V'], aggfunc='sum').fillna(0)
    df_teste['Soma'] = 0
    df_teste['Soma'] = df_teste['Valor_ajuste']['C'] + df_teste['Valor_ajuste']['V']
    df_teste['Percentual_C'] = df_teste['Valor_ajuste']['C']/df_teste['Soma']
    df_teste['Percentual_V'] = df_teste['Valor_ajuste']['V']/df_teste['Soma']
    
    df_negocio.reset_index(inplace=True)
    df_negocio.set_index(['Nota','Titulo','C/V'], inplace=True)
    df_negocio = df_negocio.join(df_teste['Percentual_C'], how='left')
    df_negocio = df_negocio.join(df_teste['Percentual_V'], how='left')
    df_negocio.reset_index(inplace=True)

    df_notas_tmp = df_resumo[['Nota','Total_bolsa','Total_Corretagem_Despesas']]
    df_notas_tmp['Custo_Total'] = df_notas_tmp['Total_bolsa'] + df_notas_tmp['Total_Corretagem_Despesas']
    df_notas_tmp.set_index('Nota', inplace=True)

    df_negocio.set_index('Nota', inplace=True)
    df_negocio = df_negocio.join(df_notas_tmp['Custo_Total'], how='left')
    df_negocio['Custo_Ponderado_C'] = abs(df_negocio['Custo_Total'] * df_negocio['Percentual_C'])
    df_negocio['Custo_Ponderado_V'] = df_negocio['Custo_Total'] * df_negocio['Percentual_V']

    df_negocio['Custo_Ponderado_V'].where(df_negocio['C/V'] != 'C',0, inplace= True)
    df_negocio['Custo_Ponderado_C'].where(df_negocio['C/V'] != 'V',0, inplace= True)
    df_negocio['Custo_Final'] = df_negocio['Custo_Ponderado_C'] + df_negocio['Custo_Ponderado_V']
    
    df_negocio.reset_index(inplace=True)
    df_negocio = df_negocio.loc[:,~df_negocio.columns.isin(['Custo_Total','Custo_Ponderado_C','Custo_Ponderado_V', 'Percentual_C','Percentual_V', 'index'])]
    df_negocio['Preco_Liquido_Pago_Recebido'] = df_negocio['Valor_ajuste'] + df_negocio['Custo_Final']
    df_negocio['Preco_Liquido_Pago_Recebido_Unitario'] = df_negocio['Preco_Liquido_Pago_Recebido']/df_negocio['Qtde']

    return df_negocio