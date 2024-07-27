from flask import Flask, jsonify, redirect, render_template, request, url_for
import pymysql

app = Flask(__name__)

db_config = {
    'user': 'root',
    'password': 'shuanq',
    'db': 'Crime',
    'host': '35.188.17.89',
    'port': 3306
}

output_table_cache = None
USERNAME = None

def get_db_connection():
    connection = pymysql.connect(host=db_config['host'],
                                 user=db_config['user'],
                                 password=db_config['password'],
                                 db=db_config['db'],
                                 port=db_config['port'],
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection

def update_output_table_cache():
    global output_table_cache
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM OutputTable")
            output_table_cache = cursor.fetchall()
    finally:
        connection.close()

def save_user_credentials(username, password):
    global USERNAME
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM UserInfo WHERE UserName = %s", (username,))
            USERNAME = username
            user = cursor.fetchone()
            if user is not None:
                # print(user['Password'])
                # print(password)
                if user['Password'] == password:
                    # print("equal")
                    return redirect(url_for('index'))
                else:
                    # print("neq")
                    # !fix login with wrong password 
                    return jsonify({'success': 'Login failed! Wrong Password :('}), 400
            else:
                cursor.execute("INSERT INTO UserInfo (UserName, Password) VALUES (%s, %s)", (username, password))
                connection.commit()
                return redirect(url_for('index'))
    finally:
        connection.close()


@app.route('/')
def index():
    global output_table_cache
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS OutputTable")
            cursor.execute("CREATE TABLE OutputTable LIKE CrimeTable")
            cursor.execute("INSERT INTO OutputTable SELECT * FROM CrimeTable LIMIT 5000")
        connection.commit()
        update_output_table_cache()
    finally:
        connection.close()
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    return save_user_credentials(username, password)

@app.route('/location')
def location():
    global output_table_cache
    if output_table_cache is None:
        update_output_table_cache()
    return jsonify(output_table_cache)  

@app.route('/description/<des>')
def description(des):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = "SELECT * FROM OutputTable WHERE Crime_Description LIKE %s"
            cursor.execute(query, ('%' + des + '%',))
            results = cursor.fetchall()
            return jsonify(results)
    finally:
        connection.close()

@app.route('/region/<latitude>/<longitude>/<radius>')
def region(longitude, latitude, radius):
    try:
        longitude = float(longitude)
        latitude = float(latitude)
        radius = float(radius) * 1000

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                query = """
                SELECT *, 
                    ST_Distance_Sphere(
                        POINT(%s, %s),
                        POINT(Longitude, Latitude)
                    ) AS Distance
                FROM OutputTable
                HAVING Distance <= %s
                """
                cursor.execute(query, (latitude, longitude, radius))
                results = cursor.fetchall()

                return jsonify(results)
        finally:
            connection.close()
    except Exception as e:
        app.logger.error(f'Error in region endpoint: {e}')
        return jsonify({'error': 'An error occurred processing your request'}), 500

@app.route('/delete-user', methods=['POST'])
def delete_user():
    username = request.form.get('username')
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM UserInfo WHERE UserName = %s", (username,))
            connection.commit()
            if cursor.rowcount > 0:
                return jsonify({'success': 'User deleted successfully :)'}), 200
            else:
                return jsonify({'error': 'User not found :('}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()
        
# @app.route('/possible-gun-crimes')
# def possible_gun_crimes():
#     connection = get_db_connection()
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT * FROM GunCrimes JOIN OutputTable ON OutputTable.DR_NO = GunCrimes.DR_NO WHERE Possible_Gun_Related = 1")
#             results = cursor.fetchall()
#             return jsonify(results)
#     finally:
#         connection.close()

@app.route('/confirmed-gun-crimes')
def confirmed_gun_crimes():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM GunCrimes JOIN OutputTable ON OutputTable.DR_NO = GunCrimes.DR_NO WHERE Gun_Related = 1")
            results = cursor.fetchall()
            return jsonify(results)
    finally:
        connection.close()

@app.route('/insert-crime', methods=['POST'])
def insert_crime():
    dr_no = request.form['dr_no']
    crime_description = request.form['crime_description']
    longitude = request.form['longitude']
    latitude = request.form['latitude']
    comment = request.form['comment']
    date_occ = request.form['date_occ']

    connection = get_db_connection()
    try:
        longitude = float(longitude)
        latitude = float(latitude)
        
        if dr_no == None:
            return jsonify({'error': 'insert a crime id'}), 400
        
        with connection.cursor() as cursor:
            insert_update_query = """
            INSERT INTO CrimeTable (DR_NO, Crime_Description, Longitude, Latitude, Comment, Date_Occ)
            VALUES (%s, %s, %s, %s, %s, STR_TO_DATE(%s, '%%Y-%%m-%%d'))
            ON DUPLICATE KEY UPDATE 
                Crime_Description = VALUES(Crime_Description),
                Longitude = VALUES(Longitude),
                Latitude = VALUES(Latitude),
                Comment = VALUES(Comment),
                Date_Occ = VALUES(Date_Occ)
            """
            cursor.execute(insert_update_query, (dr_no, crime_description, longitude, latitude, comment, date_occ))
            connection.commit()

            response_message = 'Crime case insert/update successfully'

        return jsonify({'success': response_message})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()


if __name__ == '__main__':
    app.run(debug=True)
