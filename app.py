from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import qrcode
import io
import base64

votes = {}

app = Flask(__name__)

# SQLite database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting_results.db'
db = SQLAlchemy(app)

# Create a model for the voting results table
class VoteResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_votes = db.Column(db.Integer, default=1)

# Create the database tables (only needed once)
def create_table():
    db.create_all()

# Global dictionary to store the scores (for debugging)
scores = {}

def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_byte_array = io.BytesIO()
    img.save(img_byte_array, format='PNG')
    return base64.b64encode(img_byte_array.getvalue()).decode()

@app.route('/')
def index():
    voting_page_url = request.url_root + 'vote'
    qr_code = generate_qr_code(voting_page_url)
    return render_template('index.html', qr_code=qr_code)

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if request.method == 'POST':
        participant_name = request.form.get('name', '')
        score = int(request.form.get('score', 0))

        # Check if the participant already exists in the database
        existing_vote = VoteResult.query.filter_by(participant_name=participant_name).first()

        if existing_vote:
            # Update the score and total votes for the existing participant
            existing_vote.score += score
            existing_vote.total_votes = (existing_vote.total_votes or 0) + 1  # Ensure total_votes is not None
        else:
            # Create a new vote result for the participant
            vote_result = VoteResult(participant_name=participant_name, score=score)
            db.session.add(vote_result)

        db.session.commit()

        # Redirect to the results page after voting
        return redirect(url_for('results'))
    return render_template('vote.html')

@app.route('/results')
def results():
    all_results = VoteResult.query.all()

    # Dictionary to store participant-wise votes and scores
    participant_data = {}

    # Calculate the total votes and weighted score for each participant
    for result in all_results:
        participant_name = result.participant_name
        total_votes = result.total_votes or 0
        score = result.score or 0
        weighted_score = total_votes * score

        if participant_name not in participant_data:
            participant_data[participant_name] = {
                'total_votes': total_votes,
                'weighted_score': weighted_score,
            }
        else:
            participant_data[participant_name]['total_votes'] += total_votes
            participant_data[participant_name]['weighted_score'] += weighted_score

    # Calculate the final weighted average for each participant
    for participant in participant_data:
        total_votes = participant_data[participant]['total_votes']
        weighted_score = participant_data[participant]['weighted_score']

        if total_votes > 0:
            weighted_average = weighted_score / total_votes
        else:
            weighted_average = 0

        participant_data[participant]['weighted_average'] = weighted_average

    # Pass the participant_data dictionary to the 'results.html' template
    return render_template('results.html', participant_data=participant_data)




if __name__ == "__main__":
    with app.app_context():
        db.create_all()

app.run(host='0.0.0.0', port=8000, debug=True)
migrate = Migrate(app, db)