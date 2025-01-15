import requests
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("JSONParser")

def fetch_linkedin_jobs(JOB_URL, RAPIDKEY, RAPIDHOST):
    vacancies=[]
    querystring = {
        "query":"Frontend",
        "location":"Worlwide",
        "autoTranslateLocation":"true",
        "remoteOnly":"true",
        "employmentTypes":"fulltime;parttime;intern;contractor",
        "datePosted":"week"
    }
    headers={"x-rapidapi-key": RAPIDKEY, "x-rapidapi-host": RAPIDHOST}

    
    while True:
        try:
            req = requests.Request('GET', JOB_URL,headers=headers, params=querystring)
            prepared = req.prepare()
            logger.info(f'Запрос ленты: {prepared.url}')
            response = requests.get(url,headers=headers, params=querystring)
            logger.info(f'response: {response}')
            response.raise_for_status()
            
            # Debugging: Log the response content
            logger.debug(f'Response content: {response.content}')
            data = response.json()
            logger.info(f'response: {data}')
            if 'jobs' not in data or not data['jobs']:
                logger.info('No vacancies found in the response.')
                break
            for item in data['jobs']:
                vacancies.append((item['title'], item['jobProviders'][0]['url']))
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе JSON {url}: {e}")
            break
    return vacancies