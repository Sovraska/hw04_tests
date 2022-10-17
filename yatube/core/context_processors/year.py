import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': int(str(datetime.date.today())[:4])
    }
