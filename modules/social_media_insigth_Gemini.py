import requests
import time
import urllib.parse
import google.generativeai as genai

# Configurações
ACCESS_TOKEN = 'IGQWRPMzRhSE5nRTJ6YkxGQTJ1ckl2Qko5YW5aY3lpaENHVF9xRzl5bjlIUkZAEVndrZA2VHTVN0YTRkUVFrM2w4TXB1VXJZAMC1WajNxTWJ6X2RQbk5QdlBNQTRiLV9NSUdjWkhZAVnhSbDNFNkxTTUpRd0l4d3dhbHMZD'
INSTAGRAM_BUSINESS_ID = '17841471051465122'
API_VERSION = 'v21.0'
BASE_URL = f'https://graph.instagram.com/{API_VERSION}'

# Configure a API Key do Google Generative AI diretamente no código
genai.configure(api_key="AIzaSyAGNRiMrrzC5Xk8GZhd3Tsi46p0TSDtzPE")
model = genai.GenerativeModel("gemini-1.5-flash")

# Disclaimer fixo a ser adicionado em todas as legendas
DISCLAIMER = "\n\n⚠️ **Aviso:** Todas as imagens e as notícias foram geradas com inteligência artificial com base em dados climáticos reais."

def generate_caption(data_json):
    prompt = (
        "Analise os dados a seguir e crie uma notícia sobre o impacto positivo ou negativo para as pessoas no ambiente urbano: "
        f"{data_json}"
    )
    response = model.generate_content(prompt)
    caption = response.text.strip()
    return caption

# Função para gerar a URL da imagem com a Pollinations API
def generate_image(caption):
    prompt = (
        "Crie um prompt com no máximo 6 palavras para que a IA generativa Pollinations faça uma imagem para a seguinte notícia: "
        f"{caption}"
    )
    response = model.generate_content(prompt)
    if not hasattr(response, 'text') or not response.text:
        print('Erro ao gerar prompt para a imagem:', response)
        return None

    encoded_prompt = urllib.parse.quote(response.text.strip())
    url = f'https://image.pollinations.ai/prompt/{encoded_prompt}'
    img_response = requests.get(url)
    if img_response.status_code == 200:
        # Supondo que a API retorne uma URL pública da imagem gerada
        print('Imagem gerada com sucesso.')
        return img_response.url  # Retorna a URL da imagem gerada
    else:
        print('Erro ao gerar imagem:', img_response.text)
        return None

# Função para verificar se a imagem está acessível
def verify_image_url(url):
    try:
        response = requests.head(url)
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            print('URL da imagem verificada com sucesso.')
            return True
        else:
            print('URL da imagem inválida ou inacessível:', response.status_code)
            return False
    except requests.RequestException as e:
        print('Erro ao verificar a URL da imagem:', e)
        return False

# Criar um Container de Mídia
def create_media_container(img_url, caption):
    url = f'{BASE_URL}/{INSTAGRAM_BUSINESS_ID}/media'
    payload = {
        'image_url': img_url,
        'caption': caption,
        'access_token': ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        media_id = response.json().get('id')
        print(f'Container de mídia criado: {media_id}')
        return media_id
    else:
        print('Erro ao criar container de mídia:', response.text)
        return None

# Publicar o Container de Mídia
def publish_media(media_id):
    url = f'{BASE_URL}/{INSTAGRAM_BUSINESS_ID}/media_publish'
    payload = {
        'creation_id': media_id,
        'access_token': ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        post_id = response.json().get('id')
        print(f'Post publicado com ID: {post_id}')
        return post_id
    else:
        print('Erro ao publicar mídia:', response.text)
        # Opcional: Implementar verificação de status_code aqui
        return None

# Verificar o status de publicação do contêiner
def check_publishing_status(container_id):
    url = f'{BASE_URL}/{container_id}'
    params = {
        'fields': 'status_code',
        'access_token': ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        status = response.json().get('status_code')
        print(f'Status do contêiner: {status}')
        return status
    else:
        print('Erro ao verificar status do contêiner:', response.text)
        return None

def generate_social_media_insight(data_json):
    # Etapa 1: Gerar a Legenda com base nos dados
    original_caption = generate_caption(data_json)
    print('Legenda gerada:', original_caption)
    
    # Concatenar o disclaimer à legenda
    caption = original_caption + DISCLAIMER
    print('Legenda final:', caption)
    
    # Etapa 2: Gerar a URL da Imagem
    img_url = generate_image(original_caption)
    if not img_url:
        print('Falha ao gerar a imagem. Encerrando o processo.')
        return
    
    # Verificar se a URL da imagem é acessível
    if not verify_image_url(img_url):
        print('URL da imagem inválida. Encerrando o processo.')
        return
    
    # Etapa 3: Criar um Container de Mídia
    media_id = create_media_container(img_url, caption)
    if not media_id:
        print('Falha ao criar o container de mídia. Encerrando o processo.')
        return
    
    # Opcional: Aguardar um breve período antes de publicar
    time.sleep(5)
    
    # Etapa 4: Publicar o Container de Mídia
    post_id = publish_media(media_id)
    if not post_id:
        print('Falha ao publicar a mídia. Verificando status do contêiner.')
        status = check_publishing_status(media_id)
        if status:
            if status == 'FINISHED':
                post_id = publish_media(media_id)
                if post_id:
                    print(f'Post publicado com ID: {post_id}')
            elif status in ['ERROR', 'EXPIRED']:
                print(f'Não foi possível publicar o contêiner. Status: {status}')
            elif status == 'IN_PROGRESS':
                print('A publicação ainda está em andamento. Tente novamente mais tarde.')
            elif status == 'PUBLISHED':
                print('O contêiner já foi publicado.')
        return
    
    return post_id

def main():
    # Exemplo de dados JSON (substitua com os dados reais)
    dados_climaticos = {
        "evento": "Alagamento",
        "local": "Marte",
        "impacto": "Negativo",
        "descrição": "Alagamento causou danos significativos à infraestrutura urbana."
    }
    generate_social_media_insight(dados_climaticos)

if __name__ == '__main__':
    main()
