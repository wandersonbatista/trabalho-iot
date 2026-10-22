import pandas as pd

print("Iniciando a limpeza do dataset NGSIM...")

# Lê o CSV forçando o tipo string para não perder a formatação original
df = pd.read_csv('ngsim_lankershim.csv', dtype=str)

def converter_para_float(valor):
    if pd.isna(valor): return 0.0
    v = str(valor).strip()
    
    # 1. Caso com ponto e vírgula simultâneos (ex: 2.042,59 ou 2,042.59)
    if ',' in v and '.' in v:
        if v.rfind(',') > v.rfind('.'): # Vírgula é a casa decimal
            v = v.replace('.', '').replace(',', '.')
        else: # Ponto é a casa decimal
            v = v.replace(',', '')
            
    # 2. Caso apenas com vírgula (ex: 7,52)
    elif ',' in v:
        v = v.replace(',', '.')
        
    # 3. Caso com múltiplos pontos (ex: 2.042.594 que deveria ser 2042.594)
    elif v.count('.') > 1:
        partes = v.rsplit('.', 1) # Separa apenas no último ponto
        v = partes[0].replace('.', '') + '.' + partes[1]
        
    return float(v)

# Aplica a limpeza nas duas colunas que os sensores vão consumir
df['v_Vel'] = df['v_Vel'].apply(converter_para_float)
df['Local_Y'] = df['Local_Y'].apply(converter_para_float)

# Salva o dataset "Padrão Ouro" para a simulação
df.to_csv('ngsim_limpo.csv', index=False)
print("Dataset padronizado com sucesso! Arquivo 'ngsim_limpo.csv' gerado.")