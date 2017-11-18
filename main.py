from app import app #Импорт нашего Flask app
import views
#
# def redirect_url(default='index'):
#     return request.args.get('next') or \
#            request.referrer or \
#            url_for(default)

if __name__ == '__main__':
    app.run()
