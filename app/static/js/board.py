from browser import document, alert

def on_click(ev):
    document[ev.target.id].attrs['fill'] = "black"

for x in [1,2,3,4,5]:
    for y in [1,2,3,4,5]:
        ident = "space_{}_{}".format(x,y)
        document[ident].bind("click", echo)

