from app.main import create_app

frontend_app = create_app()

if __name__ == '__main__':
    frontend_app.run('0.0.0.0', port=5000)
