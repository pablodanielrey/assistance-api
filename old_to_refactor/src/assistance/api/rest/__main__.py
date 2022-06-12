
import ptvsd
ptvsd.enable_attach(address = ('0.0.0.0', 10304))

from assistance.api.rest.wsgi import app
app.run(host='0.0.0.0', port=10302, debug=False)

