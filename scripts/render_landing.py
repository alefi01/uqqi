"""Рендер главной в .design-gate для дизайн-гейтов (полный и пустой варианты)."""
import json, os
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'), autoescape=True)
t = env.get_template('landing.html')
works = [
  {"slug":"boroda","title":"Барбершоп «Борода»","city":"Саранск","design_name":"Barber","year":"2026",
   "shots":["/static/reviews/boroda.svg","/static/reviews/motor.svg"]},
  {"slug":"motor","title":"Автосервис «Мотор»","city":"Казань","design_name":"Garage","year":"2026",
   "shots":["/static/reviews/motor.svg"]},
  {"slug":"hleb","title":"Пекарня «Тёплый хлеб»","city":"Москва","design_name":"Patisserie","year":"2026",
   "shots":["/static/reviews/hleb.svg"]},
]
ctx = dict(request=None, stats={"sites":128,"cities":37,"minutes":"3,8"},
           reviews=json.load(open('content/reviews.json')),
           plans={"month":{"amount":"399.00"},"quarter":{"amount":"999.00"},"year":{"amount":"3590.00"}})
os.makedirs('.design-gate', exist_ok=True)


def local(html: str) -> str:
    """Гейты открывают файл по file://, поэтому /static/ надо развернуть в
    абсолютный путь — иначе картинки не грузятся и глазами ничего не видно."""
    return html.replace('src="/static/', 'src="file://' + os.path.abspath('static') + '/') \
               .replace("url('/static/", "url('file://" + os.path.abspath('static') + "/")


open('.design-gate/landing.html','w').write(local(t.render(works=works, **ctx)))
open('.design-gate/landing-empty.html','w').write(local(t.render(works=[], **dict(ctx, reviews=[]))))
print('rendered .design-gate/landing.html + landing-empty.html')
