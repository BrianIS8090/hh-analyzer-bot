import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os
from datetime import datetime
from typing import List, Dict

# Регистрируем шрифт для кириллицы
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont('DejaVu', FONT_PATH))
    FONT_NAME = 'DejaVu'
else:
    FONT_NAME = 'Helvetica'


def generate_salary_distribution_chart(salaries: list, output_path: str = None) -> BytesIO:
    """Генерация графика распределения зарплат"""
    
    if not salaries:
        return None
    
    plt.figure(figsize=(10, 6))
    plt.hist(salaries, bins=20, color='#3B82F6', edgecolor='white', alpha=0.8)
    plt.xlabel('Зарплата, ₽', fontsize=12)
    plt.ylabel('Количество вакансий', fontsize=12)
    plt.title('Распределение зарплат', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf


def generate_salary_by_experience_chart(salary_by_exp: dict, output_path: str = None) -> BytesIO:
    """Генерация графика зарплат по опыту"""
    
    if not salary_by_exp:
        return None
    
    exp_order = ["Без опыта", "1-3 года", "3-6 лет", "6+ лет"]
    data = {k: v for k, v in salary_by_exp.items() if k in exp_order}
    
    if not data:
        return None
    
    labels = [k for k in exp_order if k in data]
    mins = [data[k]['min'] for k in labels]
    maxs = [data[k]['max'] for k in labels]
    avgs = [data[k]['avg'] for k in labels]
    
    x = range(len(labels))
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    width = 0.25
    ax.bar([i - width for i in x], mins, width, label='Минимум', color='#22C55E', alpha=0.8)
    ax.bar(x, avgs, width, label='Средняя', color='#3B82F6', alpha=0.8)
    ax.bar([i + width for i in x], maxs, width, label='Максимум', color='#EF4444', alpha=0.8)
    
    ax.set_xlabel('Опыт работы', fontsize=12)
    ax.set_ylabel('Зарплата, ₽', fontsize=12)
    ax.set_title('Зарплаты по уровню опыта', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf


def generate_top_companies_chart(companies: list, output_path: str = None) -> BytesIO:
    """Генерация графика топ работодателей"""
    
    if not companies:
        return None
    
    top_10 = companies[:10]
    names = [c[0][:20] + '...' if len(c[0]) > 20 else c[0] for c in top_10]
    counts = [c[1] for c in top_10]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    y_pos = range(len(names))
    ax.barh(y_pos, counts, color='#8B5CF6', alpha=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel('Количество вакансий', fontsize=12)
    ax.set_title('Топ-10 работодателей', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Добавляем значения на бары
    for i, v in enumerate(counts):
        ax.text(v + 0.5, i, str(v), va='center')
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf


def generate_skills_chart(skills: list, output_path: str = None) -> BytesIO:
    """Генерация графика топ навыков"""
    
    if not skills:
        return None
    
    top_15 = skills[:15]
    names = [s[0] for s in top_15]
    counts = [s[1] for s in top_15]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    y_pos = range(len(names))
    ax.barh(y_pos, counts, color='#F59E0B', alpha=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel('Количество упоминаний', fontsize=12)
    ax.set_title('Топ-15 востребованных навыков', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    for i, v in enumerate(counts):
        ax.text(v + 0.5, i, str(v), va='center')
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf


def generate_pdf_report(
    query: str,
    area: str,
    stats: dict,
    vacancies: List[dict],
    output_path: str = None
) -> BytesIO:
    """Генерация PDF отчёта с аналитикой"""
    
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    # Стили
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=18,
        spaceAfter=12,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        spaceAfter=6
    )
    
    story = []
    
    # Заголовок
    story.append(Paragraph(f"Аналитика вакансий: {query}", title_style))
    if area:
        story.append(Paragraph(f"Город: {area}", normal_style))
    story.append(Paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style))
    story.append(Paragraph(f"Всего вакансий: {stats['total']}", normal_style))
    story.append(Spacer(1, 20))
    
    # Зарплаты
    salary = stats.get("salary", {})
    if salary.get("available"):
        story.append(Paragraph("1. Статистика зарплат", heading_style))
        
        salary_data = [
            ["Показатель", "Значение"],
            ["Минимальная", f"{salary['min']:,} ₽"],
            ["Максимальная", f"{salary['max']:,} ₽"],
            ["Средняя", f"{salary['avg']:,} ₽"],
            ["Медиана", f"{salary['median']:,} ₽"],
        ]
        
        if salary.get("from_avg"):
            salary_data.append(["Средняя 'от'", f"{salary['from_avg']:,} ₽"])
        if salary.get("to_avg"):
            salary_data.append(["Средняя 'до'", f"{salary['to_avg']:,} ₽"])
        
        t = Table(salary_data, colWidths=[6*cm, 6*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 1, colors.white)
        ]))
        story.append(t)
        story.append(Spacer(1, 20))
        
        # График распределения зарплат
        # Для графика нужны исходные данные зарплат - пропустим пока
        
        story.append(Paragraph("Распределение по интервалам:", normal_style))
        for interval, count in salary["distribution"].items():
            pct = (count / salary["count"] * 100) if salary["count"] else 0
            story.append(Paragraph(f"• {interval}: {count} ({pct:.1f}%)", normal_style))
        story.append(Spacer(1, 20))
    
    # Зарплаты по опыту
    salary_by_exp = stats.get("salary_by_experience", {})
    if salary_by_exp:
        story.append(Paragraph("2. Зарплаты по опыту работы", heading_style))
        
        exp_data = [["Опыт", "Мин", "Макс", "Средняя", "Медиана", "Кол-во"]]
        exp_order = ["Без опыта", "1-3 года", "3-6 лет", "6+ лет", "Не указано"]
        
        for exp_name in exp_order:
            if exp_name in salary_by_exp:
                data = salary_by_exp[exp_name]
                exp_data.append([
                    exp_name,
                    f"{data['min']:,}",
                    f"{data['max']:,}",
                    f"{data['avg']:,}",
                    f"{data['median']:,}",
                    str(data['count'])
                ])
        
        t = Table(exp_data, colWidths=[3*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm, 2*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 1, colors.white)
        ]))
        story.append(t)
        story.append(Spacer(1, 20))
    
    # Топ работодателей
    companies = stats.get("companies", {})
    if companies.get("top_20"):
        story.append(Paragraph("3. Топ-20 работодателей", heading_style))
        
        company_data = [["#", "Компания", "Вакансий"]]
        for i, (name, count) in enumerate(companies["top_20"], 1):
            company_data.append([str(i), name[:40], str(count)])
        
        t = Table(company_data, colWidths=[1*cm, 10*cm, 3*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#22C55E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 1, colors.white)
        ]))
        story.append(t)
        story.append(Spacer(1, 20))
    
    # Навыки
    skills = stats.get("skills", {})
    if skills.get("top_20"):
        story.append(Paragraph("4. Топ-20 востребованных навыков", heading_style))
        
        skills_data = [["#", "Навык", "Упоминаний"]]
        for i, (name, count) in enumerate(skills["top_20"], 1):
            skills_data.append([str(i), name, str(count)])
        
        t = Table(skills_data, colWidths=[1*cm, 8*cm, 3*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F59E0B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 1, colors.white)
        ]))
        story.append(t)
        story.append(Spacer(1, 20))
    
    # Опыт
    exp = stats.get("experience", {})
    if exp:
        story.append(Paragraph("5. Требования по опыту", heading_style))
        for name, count in exp.items():
            pct = (count / stats['total'] * 100) if stats['total'] else 0
            story.append(Paragraph(f"• {name}: {count} ({pct:.1f}%)", normal_style))
        story.append(Spacer(1, 20))
    
    # График
    schedule = stats.get("schedule", {})
    if schedule:
        story.append(Paragraph("6. График работы", heading_style))
        for name, count in schedule.items():
            pct = (count / stats['total'] * 100) if stats['total'] else 0
            story.append(Paragraph(f"• {name}: {count} ({pct:.1f}%)", normal_style))
        story.append(Spacer(1, 20))
    
    # Список всех вакансий
    if vacancies:
        story.append(PageBreak())
        story.append(Paragraph("7. Список всех вакансий", heading_style))
        story.append(Spacer(1, 10))
        
        for i, v in enumerate(vacancies[:100], 1):  # Ограничиваем 100 для PDF
            name = v.get("name", "Без названия")
            employer = v.get("employer", {})
            emp_name = employer.get("name", "Не указано") if isinstance(employer, dict) else str(employer)
            salary_info = v.get("salary")
            
            if salary_info and isinstance(salary_info, dict):
                from_val = salary_info.get("from", "")
                to_val = salary_info.get("to", "")
                currency = salary_info.get("currency", "RUR")
                if from_val and to_val:
                    salary_text = f"{from_val:,} - {to_val:,} {currency}"
                elif from_val:
                    salary_text = f"от {from_val:,} {currency}"
                elif to_val:
                    salary_text = f"до {to_val:,} {currency}"
                else:
                    salary_text = "Не указана"
            else:
                salary_text = "Не указана"
            
            story.append(Paragraph(f"<b>{i}. {name}</b>", normal_style))
            story.append(Paragraph(f"   Компания: {emp_name}", normal_style))
            story.append(Paragraph(f"   Зарплата: {salary_text}", normal_style))
            story.append(Spacer(1, 5))
    
    doc.build(story)
    buf.seek(0)
    
    return buf
