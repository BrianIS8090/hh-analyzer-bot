import pandas as pd
from collections import Counter
from typing import List, Dict
import re


def analyze_vacancies(vacancies: List[dict]) -> dict:
    """Анализ списка вакансий и генерация статистики"""
    
    if not vacancies:
        return {"error": "Вакансии не найдены"}
    
    df = pd.DataFrame(vacancies)
    
    stats = {
        "total": len(vacancies),
        "salary": analyze_salaries(vacancies),
        "salary_by_experience": analyze_salary_by_experience(vacancies),
        "companies": analyze_companies(vacancies),
        "experience": analyze_experience(vacancies),
        "employment": analyze_employment(vacancies),
        "schedule": analyze_schedule(vacancies),
        "skills": extract_skills(vacancies),
    }
    
    return stats


def analyze_salary_by_experience(vacancies: List[dict]) -> dict:
    """Анализ зарплат по опыту работы"""
    
    exp_map = {
        "noExperience": "Без опыта",
        "between1And3": "1-3 года",
        "between3And6": "3-6 лет",
        "moreThan6": "6+ лет"
    }
    
    # Группируем зарплаты по опыту
    salary_by_exp = {
        "Без опыта": [],
        "1-3 года": [],
        "3-6 лет": [],
        "6+ лет": [],
        "Не указано": []
    }
    
    for v in vacancies:
        # Получаем опыт
        exp_data = v.get("experience")
        if exp_data and isinstance(exp_data, dict):
            exp_id = exp_data.get("id", "Не указано")
        elif exp_data and isinstance(exp_data, str):
            exp_id = exp_data
        else:
            exp_id = "Не указано"
        
        exp_name = exp_map.get(exp_id, "Не указано")
        
        # Получаем зарплату
        salary = v.get("salary")
        if salary and isinstance(salary, dict):
            from_val = salary.get("from")
            to_val = salary.get("to")
            currency = salary.get("currency", "RUR")
            
            # Конвертируем валюту
            if currency == "USD":
                rate = 90
                from_val = from_val * rate if from_val else None
                to_val = to_val * rate if to_val else None
            elif currency == "EUR":
                rate = 100
                from_val = from_val * rate if from_val else None
                to_val = to_val * rate if to_val else None
            
            # Средняя по вилке
            if from_val and to_val:
                avg = (from_val + to_val) / 2
            elif from_val:
                avg = from_val
            elif to_val:
                avg = to_val
            else:
                continue
            
            salary_by_exp[exp_name].append(avg)
    
    # Считаем статистику по каждой группе
    import numpy as np
    result = {}
    
    for exp_name, salaries in salary_by_exp.items():
        if salaries:
            result[exp_name] = {
                "count": len(salaries),
                "min": int(min(salaries)),
                "max": int(max(salaries)),
                "avg": int(np.mean(salaries)),
                "median": int(np.median(salaries))
            }
    
    return result


def analyze_salaries(vacancies: List[dict]) -> dict:
    """Анализ зарплат"""
    
    salaries = []
    salary_from_list = []
    salary_to_list = []
    currency_stats = Counter()
    
    for v in vacancies:
        salary = v.get("salary")
        if salary:
            currency = salary.get("currency", "RUR")
            currency_stats[currency] += 1
            
            # Конвертируем в рубли для аналитики
            from_val = salary.get("from")
            to_val = salary.get("to")
            
            if currency == "USD":
                rate = 90  # Примерный курс
                from_val = from_val * rate if from_val else None
                to_val = to_val * rate if to_val else None
            elif currency == "EUR":
                rate = 100  # Примерный курс
                from_val = from_val * rate if from_val else None
                to_val = to_val * rate if to_val else None
            
            if from_val:
                salary_from_list.append(from_val)
            if to_val:
                salary_to_list.append(to_val)
            
            # Средняя зарплата по вилке
            if from_val and to_val:
                salaries.append((from_val + to_val) / 2)
            elif from_val:
                salaries.append(from_val)
            elif to_val:
                salaries.append(to_val)
    
    if not salaries:
        return {"available": False, "message": "Зарплаты не указаны"}
    
    import numpy as np
    
    return {
        "available": True,
        "count": len(salaries),
        "min": int(min(salaries)),
        "max": int(max(salaries)),
        "avg": int(np.mean(salaries)),
        "median": int(np.median(salaries)),
        "from_avg": int(np.mean(salary_from_list)) if salary_from_list else None,
        "to_avg": int(np.mean(salary_to_list)) if salary_to_list else None,
        "distribution": get_salary_distribution(salaries),
        "currencies": dict(currency_stats.most_common(5))
    }


def get_salary_distribution(salaries: List[float]) -> dict:
    """Распределение зарплат по интервалам"""
    
    dist = {
        "до 100к": 0,
        "100-150к": 0,
        "150-200к": 0,
        "200-250к": 0,
        "250-300к": 0,
        "300-400к": 0,
        "400к+": 0
    }
    
    for s in salaries:
        if s < 100000:
            dist["до 100к"] += 1
        elif s < 150000:
            dist["100-150к"] += 1
        elif s < 200000:
            dist["150-200к"] += 1
        elif s < 250000:
            dist["200-250к"] += 1
        elif s < 300000:
            dist["250-300к"] += 1
        elif s < 400000:
            dist["300-400к"] += 1
        else:
            dist["400к+"] += 1
    
    return dist


def analyze_companies(vacancies: List[dict]) -> dict:
    """Анализ работодателей"""
    
    companies = Counter()
    
    for v in vacancies:
        employer = v.get("employer")
        if employer and isinstance(employer, dict):
            name = employer.get("name", "Не указано")
        elif employer and isinstance(employer, str):
            name = employer
        else:
            name = "Не указано"
        companies[name] += 1
    
    return {
        "unique": len(companies),
        "top_20": companies.most_common(20)
    }


def analyze_experience(vacancies: List[dict]) -> dict:
    """Анализ требований по опыту"""
    
    exp_map = {
        "noExperience": "Без опыта",
        "between1And3": "1-3 года",
        "between3And6": "3-6 лет",
        "moreThan6": "6+ лет"
    }
    
    experience = Counter()
    
    for v in vacancies:
        exp_data = v.get("experience")
        if exp_data and isinstance(exp_data, dict):
            exp = exp_data.get("id", "Не указано")
        elif exp_data and isinstance(exp_data, str):
            exp = exp_data
        else:
            exp = "Не указано"
        exp_name = exp_map.get(exp, exp)
        experience[exp_name] += 1
    
    return dict(experience.most_common())


def analyze_employment(vacancies: List[dict]) -> dict:
    """Анализ типа занятости"""
    
    emp_map = {
        "full": "Полная занятость",
        "part": "Частичная занятость",
        "project": "Проектная работа",
        "volunteer": "Волонтёрство",
        "probation": "Стажировка"
    }
    
    employment = Counter()
    
    for v in vacancies:
        # employment - это словарь, не список
        emp = v.get("employment")
        if emp and isinstance(emp, dict):
            emp_name = emp_map.get(emp.get("id"), emp.get("name", "Не указано"))
            employment[emp_name] += 1
        elif emp and isinstance(emp, str):
            emp_name = emp_map.get(emp, emp)
            employment[emp_name] += 1
    
    return dict(employment.most_common())


def analyze_schedule(vacancies: List[dict]) -> dict:
    """Анализ графика работы"""
    
    schedule = Counter()
    
    for v in vacancies:
        sched = v.get("schedule")
        if sched and isinstance(sched, dict):
            name = sched.get("name", "Не указано")
            schedule[name] += 1
        elif sched and isinstance(sched, str):
            schedule[sched] += 1
    
    return dict(schedule.most_common())


def extract_skills(vacancies: List[dict]) -> dict:
    """Извлечение навыков из описания"""
    
    # Популярные навыки для поиска
    tech_skills = [
        "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "php", "ruby",
        "react", "vue", "angular", "node.js", "django", "flask", "fastapi", "spring", "laravel",
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "kafka", "rabbitmq",
        "docker", "kubernetes", "aws", "azure", "gcp", "linux", "git", "ci/cd", "jenkins",
        "machine learning", "ml", "ai", "data science", "pytorch", "tensorflow", "pandas", "numpy",
        "rest api", "graphql", "microservices", "mongodb", "postgresql", "redis",
        "agile", "scrum", "kanban", "jira", "confluence",
        "english", "английский", "b2", "c1", "ielts"
    ]
    
    skill_counter = Counter()
    
    for v in vacancies:
        # Ищем в сниппете
        snippet = v.get("snippet")
        if snippet and isinstance(snippet, dict):
            requirement = (snippet.get("requirement") or "").lower()
            responsibility = (snippet.get("responsibility") or "").lower()
            text = requirement + " " + responsibility
            
            for skill in tech_skills:
                if skill.lower() in text:
                    skill_counter[skill.upper()] += 1
    
    return {
        "top_20": skill_counter.most_common(20),
        "total_found": len(skill_counter)
    }


def format_stats_report(stats: dict, query: str, area: str = None) -> str:
    """Форматирование отчёта для Telegram"""
    
    lines = [
        f"📊 <b>Аналитика вакансий</b>",
        f"",
        f"🔍 Запрос: <b>{query}</b>",
    ]
    
    if area:
        lines.append(f"📍 Город: {area}")
    
    lines.append(f"📋 Всего найдено: <b>{stats['total']}</b>")
    lines.append("")
    
    # Зарплаты
    salary = stats.get("salary", {})
    if salary.get("available"):
        lines.append("💰 <b>Зарплаты:</b>")
        lines.append(f"   Мин: {salary['min']:,} ₽")
        lines.append(f"   Макс: {salary['max']:,} ₽")
        lines.append(f"   Средняя: {salary['avg']:,} ₽")
        lines.append(f"   Медиана: {salary['median']:,} ₽")
        lines.append("")
        
        lines.append("📈 <b>Распределение:</b>")
        for interval, count in salary["distribution"].items():
            pct = (count / salary["count"] * 100) if salary["count"] else 0
            bar = "█" * int(pct / 5)
            lines.append(f"   {interval}: {count} ({pct:.0f}%) {bar}")
        lines.append("")
    
    # Опыт
    exp = stats.get("experience", {})
    if exp:
        lines.append("👔 <b>Опыт работы:</b>")
        for name, count in list(exp.items())[:5]:
            lines.append(f"   {name}: {count}")
        lines.append("")
    
    # Зарплаты по опыту
    salary_by_exp = stats.get("salary_by_experience", {})
    if salary_by_exp:
        lines.append("💰 <b>Зарплаты по опыту:</b>")
        exp_order = ["Без опыта", "1-3 года", "3-6 лет", "6+ лет", "Не указано"]
        for exp_name in exp_order:
            if exp_name in salary_by_exp:
                data = salary_by_exp[exp_name]
                lines.append(f"   <b>{exp_name}:</b> {data['min']:,} - {data['max']:,} ₽")
                lines.append(f"      Средняя: {data['avg']:,} ₽ | Медиана: {data['median']:,} ₽ | ({data['count']} вакансий)")
        lines.append("")
    
    # График
    schedule = stats.get("schedule", {})
    if schedule:
        lines.append("🕐 <b>График:</b>")
        for name, count in list(schedule.items())[:5]:
            lines.append(f"   {name}: {count}")
        lines.append("")
    
    # Топ компаний
    companies = stats.get("companies", {})
    if companies.get("top_20"):
        lines.append("🏢 <b>Топ-10 работодателей:</b>")
        for name, count in companies["top_20"][:10]:
            lines.append(f"   {name}: {count} вакансий")
        lines.append("")
    
    # Навыки
    skills = stats.get("skills", {})
    if skills.get("top_20"):
        lines.append("🛠 <b>Топ-15 навыков:</b>")
        for name, count in skills["top_20"][:15]:
            lines.append(f"   {name}: {count}")
    
    return "\n".join(lines)
