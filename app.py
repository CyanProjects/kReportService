from create_app import create_app

app = create_app()

if __name__ == '__main__':
    app.run('0.0.0.0', 51490, True, use_reloader=True)
