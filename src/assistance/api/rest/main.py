import connexion

capp = connexion.App(__name__, specification_dir='./')
capp.add_api('swagger.yaml')
app = capp.app

@capp.route('/')
def home():
    return ('no permitido', 403)

def main():
    app.run(host='0.0.0.0', port=10302, debug=False)

if __name__ == '__main__':
    main()    