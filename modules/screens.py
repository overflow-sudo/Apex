"""Ekran sekmesi: monitörleri tek tek seç veya hepsini aç."""
from core import display
from core.registry import tab, action


@tab("screens", "Ekran", icon="monitor", order=20)
def view():
    mons = display.list_monitors()
    return [
        {
            "type": "tiles",
            "title": "Sadece bu ekran",
            "fill": True,
            "items": [{
                "title": m["label"],
                "sub": "%s · %s Hz%s%s" % (m["res"], m["hz"], " · ana ekran" if m["primary"] else "",
                                          "" if m["active"] else " · kapalı"),
                "icon": "monitor",
                "active": m["active"],
                "action": "screen.only",
                "params": {"name": m["name"]},
            } for m in mons],
        },
        {
            "type": "buttons",
            "items": [{"title": "Hepsini aç", "icon": "desktop", "action": "screen.all"}],
        },
    ]


@action("screen.only")
def only(name):
    display.only(name)


@action("screen.all")
def all_():
    display.enable_all()
