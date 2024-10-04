import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import requests

nest_asyncio.apply()  # تطبيق nest_asyncio هنا

TMDB_API_KEY = '6c838f76f3106bde0c80a470ddfefa35'

GENRES = {
    "خيال علمي": "878",
    "نفسي": "10749",
    "أكشن": "28",
    "كوميديا": "35",
    "دراما": "18",
    "رومانسي": "10749",
    "رعب": "27",
    "غموض": "9648",
    "مغامرة": "12"
}

async def start(update: Update, context):
    keyboard = [[InlineKeyboardButton(genre, callback_data=genre) for genre in GENRES.keys()]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر تصنيف الفلم:", reply_markup=reply_markup)

async def choose_year(update: Update, context):
    query = update.callback_query
    await query.answer()
    genre = query.data
    context.user_data['genre'] = genre
    await query.edit_message_text("أدخل سنة الإصدار:")

async def search_movie(update: Update, context):
    year = update.message.text
    genre = context.user_data['genre']
    
    movie_data = search_movies(GENRES[genre], year)

    if movie_data:
        reply = f"🎬 *اسم الفلم:* {movie_data['title']}\n\n"
        reply += f"📝 *القصة:* {movie_data['overview_ar']}\n\n"
        reply += f"📅 *سنة الإصدار:* {movie_data['release_date']}\n"
        reply += f"⭐ *التقييم:* {movie_data['rating']}/10\n\n"
        reply += f"📜 *التصنيفات:* {', '.join(movie_data['genres'])}\n"  # إضافة التصنيفات
        reply += f"👤 *أبطال الفيلم:* {', '.join(movie_data['cast'])}\n\n"
        reply += f"🔗 [رابط مشاهدة الفلم]({movie_data['url']})\n\n"

        keyboard = [[InlineKeyboardButton("فيلم آخر", callback_data='another_movie')]]  # زر فيلم آخر
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(photo=movie_data['poster_url'], caption=reply, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text("لم يتم العثور على أفلام تناسب بحثك.")

async def another_movie(update: Update, context):
    query = update.callback_query
    await query.answer()
    await start(query, context)  # إعادة بدء عملية البحث

def search_movies(genre, year):
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={genre}&primary_release_year={year}&language=ar&include_adult=false"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            movie = data['results'][0]
            # استرداد أسماء التصنيفات من genre_ids
            genre_ids = movie['genre_ids']
            genre_names = get_genre_names(genre_ids)
            
            # التحقق من وجود "credits" قبل الوصول إليها
            cast = []
            if 'credits' in movie:
                cast = [actor['name'] for actor in movie['credits'].get('cast', [])[:3]]  # الحصول على أسماء الممثلين الرئيسيين
            
            return {
                'title': movie['title'],
                'overview_ar': movie['overview'],
                'release_date': movie['release_date'],
                'rating': movie['vote_average'],
                'poster_url': f"https://image.tmdb.org/t/p/w500{movie['poster_path']}",
                'url': f"https://www.themoviedb.org/movie/{movie['id']}",
                'genres': genre_names,
                'cast': cast,
            }
    return None

def get_genre_names(genre_ids):
    genre_names = []
    for genre_id in genre_ids:
        genre_name = get_genre_name_by_id(genre_id)
        if genre_name:
            genre_names.append(genre_name)
    return genre_names

def get_genre_name_by_id(genre_id):
    genres = {
        "878": "خيال علمي",
        "10749": "نفسي",
        "28": "أكشن",
        "35": "كوميديا",
        "18": "دراما",
        "10749": "رومانسي",
        "27": "رعب",
        "9648": "غموض",
        "12": "مغامرة"
    }
    return genres.get(str(genre_id))  # تحويل إلى سلسلة لتوافق مع المفاتيح

async def main():
    app = Application.builder().token("7738261801:AAFH2qXVptlnefb68ZYspHP9y_8anPr4mwo").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(choose_year, pattern='|'.join(GENRES.keys())))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_movie))
    app.add_handler(CallbackQueryHandler(another_movie, pattern='another_movie'))  # إضافة معالج زر فيلم آخر

    await app.initialize()
    await app.run_polling()  # استخدم run_polling بدلاً من start_polling

if __name__ == '__main__':
    asyncio.run(main())


    0655