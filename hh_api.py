import aiohttp
from typing import Optional
import asyncio
import logging
from functools import lru_cache
from datetime import datetime, timedelta

HH_API_BASE = "https://api.hh.ru"

# Настройка логирования
logger = logging.getLogger(__name__)

# Кэш для результатов поиска (в памяти)
_cache = {}
_cache_ttl = timedelta(minutes=30)

def _get_cache_key(text: str, area: Optional[str] = None, **kwargs) -> str:
    """Генерация ключа кэша"""
    key_parts = [text, str(area)]
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    return "|".join(key_parts)

def _get_from_cache(key: str) -> Optional[dict]:
    """Получить из кэша"""
    if key in _cache:
        data, timestamp = _cache[key]
        if datetime.utcnow() - timestamp < _cache_ttl:
            return data
        del _cache[key]
    return None

def _set_cache(key: str, data: dict):
    """Сохранить в кэш"""
    _cache[key] = (data, datetime.utcnow())

async def search_vacancies(
    text: str,
    area: Optional[str] = None,  # ID города или "Москва", "Санкт-Петербург"
    salary_from: Optional[int] = None,
    salary_to: Optional[int] = None,
    experience: Optional[str] = None,  # noExperience, between1And3, between3And6, moreThan6
    employment: Optional[str] = None,  # full, part, project, volunteer, probation
    schedule: Optional[str] = None,  # fullDay, shift, flexible, remote, flyInFlyOut
    page: int = 0,
    per_page: int = 100,
    use_cache: bool = True
) -> dict:
    """Поиск вакансий через HH API"""

    # Проверяем кэш только для первой страницы
    if use_cache and page == 0:
        cache_key = _get_cache_key(text, area, salary_from=salary_from, salary_to=salary_to, experience=experience, employment=employment, schedule=schedule)
        cached = _get_from_cache(cache_key)
        if cached:
            logger.info(f"Cache hit for query: {text}")
            return cached

    # Если area - название города, получаем его ID
    if area and not area.isdigit():
        area = await get_area_id(area)
        logger.info(f"Area resolved to ID: {area}")

    params = {
        "text": text,
        "page": page,
        "per_page": per_page,
    }

    if area:
        params["area"] = area
    if salary_from:
        params["salary_from"] = salary_from
    if salary_to:
        params["salary_to"] = salary_to
    if experience:
        params["experience"] = experience
    if employment:
        params["employment"] = employment
    if schedule:
        params["schedule"] = schedule

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    logger.info(f"HH API request: {HH_API_BASE}/vacancies with params: {params}")

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.get(f"{HH_API_BASE}/vacancies", params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"HH API response: found {data.get('found', 0)} vacancies, page {page}")

                    # Сохраняем в кэш только первую страницу
                    if use_cache and page == 0:
                        cache_key = _get_cache_key(text, area, salary_from=salary_from, salary_to=salary_to, experience=experience, employment=employment, schedule=schedule)
                        _set_cache(cache_key, data)

                    return data
                elif resp.status == 429:
                    logger.error(f"HH API rate limit exceeded")
                    raise Exception("Слишком много запросов к HH API. Попробуйте позже.")
                elif resp.status >= 500:
                    logger.error(f"HH API server error: {resp.status}")
                    raise Exception(f"Ошибка сервера HH API ({resp.status}). Попробуйте позже.")
                else:
                    text_error = await resp.text()
                    logger.error(f"HH API error: {resp.status} - {text_error}")
                    raise Exception(f"Ошибка HH API: {resp.status}")
    except asyncio.TimeoutError:
        logger.error(f"HH API timeout")
        raise Exception("Тайм-аут при запросе к HH API. Проверьте соединение.")
    except aiohttp.ClientError as e:
        logger.error(f"HH API connection error: {e}")
        raise Exception(f"Ошибка соединения с HH API: {str(e)}")


async def get_vacancy(vacancy_id: str) -> dict:
    """Получить детальную информацию о вакансии"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{HH_API_BASE}/vacancies/{vacancy_id}", headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                raise Exception(f"HH API error: {resp.status}")


async def get_area_id(city_name: str) -> str:
    """Получить ID города по названию"""
    # Популярные города России
    areas = {
        "москва": "1",
        "moscow": "1",
        "санкт-петербург": "2",
        "спб": "2",
        "новосибирск": "4",
        "екатеринбург": "3",
        "казань": "88",
        "нижний новгород": "66",
        "челябинск": "73",
        "самара": "50",
        "омск": "68",
        "ростов-на-дону": "76",
        "уфа": "99",
        "красноярск": "46",
        "пермь": "72",
        "воронеж": "26",
        "волгоград": "24",
        "краснодар": "53",
        "саратов": "79",
        "тюмень": "98",
        "тольятти": "86",
        "ижевск": "45",
        "барнаул": "17",
        "ульяновск": "95",
        "иркутск": "42",
        "хабаровск": "39",
        "ярославль": "104",
        "владивосток": "33",
        "махачкала": "59",
        "томск": "90",
        "оренбург": "70",
        "кемерово": "47",
        "новокузнецк": "64",
        "рязань": "78",
        "астрахань": "16",
        "набережные челны": "61",
        "пенза": "71",
        "липецк": "55",
        "киров": "49",
        "тула": "91",
        "чебоксары": "100",
        "калининград": "22",
        "брянск": "20",
        "курск": "54",
        "ульяновск": "95",
        # Удалённая работа
        "удалённо": "113",
        "удаленная работа": "113",
        "remote": "113",
    }
    
    city_lower = city_name.lower().strip()
    return areas.get(city_lower, "1")  # По умолчанию Москва


async def get_all_vacancies(
    text: str,
    area: Optional[str] = None,
    max_pages: int = 10,
    **kwargs
) -> list:
    """Получить все вакансии по запросу (несколько страниц)"""
    
    import logging
    logger = logging.getLogger(__name__)
    
    all_vacancies = []
    page = 0
    
    while page < max_pages:
        try:
            result = await search_vacancies(text=text, area=area, page=page, **kwargs)
            items = result.get("items", [])
            
            logger.info(f"Page {page}: got {len(items)} items, total found: {result.get('found', 0)}")
            
            if not items:
                break
            
            all_vacancies.extend(items)
            
            # Проверяем, есть ли ещё страницы
            if page >= result.get("pages", 1) - 1:
                break
            
            page += 1
            await asyncio.sleep(0.5)  # Не спамим API
            
        except Exception as e:
            logger.error(f"Error on page {page}: {e}")
            break
    
    logger.info(f"Total vacancies collected: {len(all_vacancies)}")
    return all_vacancies
