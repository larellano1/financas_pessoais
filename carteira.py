import pandas as pd
import numpy as np
import requests
import bs4
import time, datetime

class Modelo:

    def __init__(self, data_inicial, data_final, intervalo, frequencia, taxa_livre_risco):
        self.data_inicial = data_inicial
        self.data_final = data_final
        self.intervalo = intervalo
        self.frequencia = frequencia
        self.taxa_livre_risco = taxa_livre_risco

    def __str__(self):
        return("Inicio: {0}\nFinal: {1}\nIntervalo: {2}\nFrequencia: {3}\nTaxa Livre: {4:.2f}%".format(self.data_inicial, self.data_final, self.intervalo, self.frequencia, self.taxa_livre_risco*100))


class Pesquisa:

    def __init__(self, ativo, data_inicial, data_final, frequencia, intervalo):
        self.ativo = ativo
        self.data_inicial = data_inicial
        self.data_final = data_final
        self.frequencia = frequencia
        self.intervalo = intervalo
        self.url = "https://finance.yahoo.com/quote/{4}.SA/history?period1={0}&period2={1}&interval={2}&filter=history&frequency={3}".format(self.data_inicial, self.data_final, self.intervalo, self.frequencia, ativo)
        self.dados = self.pesquisar()

    def __str__(self):

        return("Pesquisa: {0}\n\nDados: \n{1}".format(self.url, self.dados))


    def pesquisar(self):
        html = requests.get(self.url)
        soup = bs4.BeautifulSoup(html.text, "lxml")
        df = pd.read_html((soup.table).prettify())[0]
        df.dropna(inplace=True)
        df = df[:-1]
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)
        df["Adj Close**"] = pd.to_numeric(df["Adj Close**"], errors='coerce')
        return(df)

class Carteira:

    def __init__(self, nome, ativos, qtdes, modelo):

        self.modelo = modelo
        self.nome = nome
        self.ativos = ativos
        self.qtdes = qtdes
        self.pesos = np.array(qtdes)/sum(qtdes)
        self.precos = self.precos(self.ativos, self.modelo)
        self.retornos_ativos = self.log_retornos(self.precos)
        self.medias = self.mean_retornos(self.retornos_ativos)
        self.covariance = self.covariance(self.retornos_ativos)
        self.retorno_carteira = self.retorno_carteira()
        self.risco_carteira = self.risco_carteira()
        self.retornos_carteira = self.retornos_carteira()
        self.valor_carteira = self.valor_carteira()


    def __str__(self):
        return "Carteira: {0}\nAtivos: {1}\nQtdes: {2}\nPesos: {3}\nRetorno: {4:.5f}%\nRisco: {5:.5f}%\nValor: R${6:.2f}".format(self.nome, self.ativos, self.qtdes, self.pesos, self.retorno_carteira*100, self.risco_carteira.item((0,0))*100, self.valor_carteira)

    def precos(self, ativos, modelo):
        data = {}
        df = pd.DataFrame()
        controle = False
        for ativo in ativos:
            modelo = modelo
            pesquisa = Pesquisa(ativo, modelo.data_inicial, modelo.data_final, modelo.frequencia, modelo.intervalo)
            data[ativo] = pesquisa.dados["Adj Close**"]
            if(not controle):
                df = pd.DataFrame(data)
                controle = True
            else:
                df = df.merge(data[ativo], how="inner", on="Date")
                df = df.rename(columns = {"Date": "Date", "Adj Close**" : ativo})
        df = df.dropna()
        return(df)

    def log_retornos(self, data):
         return(data.pct_change()[1:])

    def mean_retornos(self, data):
        return(data.mean())

    def covariance(self, data):
        return(data.cov())

    def retorno_carteira(self):
        retorno_medio = self.medias.to_numpy()
        pesos = np.array(self.pesos)
        return(np.dot(retorno_medio, pesos))

    def risco_carteira(self):
        pesos = np.matrix(self.pesos)
        covariance = self.covariance.to_numpy()
        risco = np.matmul(np.matmul(pesos, covariance), np.transpose(pesos))
        return(risco)

    def retornos_carteira(self):
        pesos = np.matrix(self.pesos)
        df = self.retornos_ativos
        retornos_ativos = df.to_numpy()
        df["Carteira"] = np.matmul(retornos_ativos, np.transpose(pesos))
        retornos_carteira = df["Carteira"]
        return(retornos_carteira)

    def valor_carteira(self):
        qtdes = np.array(self.qtdes)
        precos = np.array(self.precos[-1:])[0]
        valor = np.dot(qtdes, precos)
        return(valor)

    def correlacao(self, carteira):
        retornos_carteira = pd.DataFrame(self.retornos_carteira)
        retornos_comparacao = pd.DataFrame(carteira.retornos_carteira)
        retornos_carteira = retornos_carteira.merge(retornos_comparacao, how="inner", on="Date")
        corr = retornos_carteira.iloc[:,0].corr(retornos_carteira.iloc[:,1])
        return(corr)

##################################

if __name__ == '__main__':

    ##Define dados para modelo
    data_inicial = round(time.mktime((datetime.datetime(2020,5,1)).timetuple()))
    data_final = round(time.mktime((datetime.datetime(2020,10,1)).timetuple()))
    intervalo = "1mo" #options: 1d 1wk 1mo
    frequencia = "1mo" #options: 1d 1wk 1mo
    taxa_livre_risco = (1+0.06)**(1/12)-1

    ##Inicia modelo
    modelo1 = Modelo(data_inicial, data_final, frequencia, intervalo, taxa_livre_risco)
    print(modelo1)

    ##Inicia carteira
    ativos = ["VALE3", "PETR4", "ABEV3", "B3SA3", "BBAS3", "BBDC4", "BOVA11", "BRFS3", "BRML3", "CCRO3", "COGN3", "CYRE3", "DTEX3", "EMBR3", "ITUB4", "JNJB34", "LREN3", "MGLU3", "NTCO3", "PCAR3", "SBSP3", "SMAL11"]
    qtdes = [500, 700, 500, 400, 300, 780, 620, 400, 149, 500, 2100, 600, 440, 400, 750, 9, 500, 1200, 600, 200, 200, 250]
    carteira1 = Carteira("Carteira 1", ativos, qtdes, modelo = modelo1)

    ##Resultados
    carteira2 = Carteira("Carteira 2", ["BOVA11"], [1000], modelo = modelo1)
    print(carteira1)
    print(carteira2)
    print("Correlação com BOVA11: {0:.2f}%".format(carteira1.correlacao(carteira2)*100))
