from flask import Flask, session, render_template, request, redirect, url_for
import os
import random

app = Flask(__name__)
app.secret_key = '뭐_세션_비밀번호를_하드코딩하는_바보가_있다고?_그럴_리가_없잖아_ㅋㅋㅋㅋㅋ' # 애초에 세션 값 별로 안 중요함.

# 확률 백분율임.
PROB_MEMORIZED = 0.2      # 이건 나중에 설정 가능하게. 많이 볼거면 0.5정도로 올리고, 안 볼거면 0 이런식으로 세션에 설정 값 저장 기능 넣으면 될듯.
PROB_NOT_MEMORIZED = 1    # 이건 걍 하드코딩 해둬도 될듯.

# BASE_DIR: data 폴더 (절대 경로) (지피티쟝이 이렇게 해줌)
BASE_DIR = os.path.join(os.getcwd(), "data")

# 기본 파일 경로. 튜토리얼 같은 거 넣어도 될 거 같은데 ㅁ?ㄹ
DEFAULT_FILE_PATH = os.path.join(BASE_DIR, "word/n2/test.txt")

def initialize_session():
    file_path = session.get('FILE_PATH', DEFAULT_FILE_PATH)
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    line_count = len(lines)
    
    if 'unread_indices' not in session:
        session['unread_indices'] = list(range(line_count))
    if 'memorized_indices' not in session:
        session['memorized_indices'] = []
    if 'not_memorized_indices' not in session:
        session['not_memorized_indices'] = []
    return lines

def get_new_word():
    lines = initialize_session()
    unread = session.get('unread_indices')
    if not unread:
        return None  # 암기 큐 비면 종료
    rand = random.randint(0, len(unread) - 1)
    idx = unread.pop(rand)
    session['unread_indices'] = unread
    session['current_index'] = idx
    return lines[idx].strip()

# 언젠가 사용되는 날이 올거야.
@app.route('/')
def root():
    return redirect(url_for('browse', path="word"))

# txt 조회용. gpt가 적당히 디렉터리 리스팅 막아줌.
@app.route('/browse')
def browse():
    # 쿼리 파라미터로 전달된 상대 경로 (기본값은 빈 문자열)
    rel_path = request.args.get('path', '')
    # BASE_DIR를 기준으로 상대 경로를 합침
    requested_path = os.path.realpath(os.path.join(BASE_DIR, rel_path))
    # 보안을 위해, requested_path가 BASE_DIR 내부에 있는지 확인
    if not requested_path.startswith(os.path.realpath(BASE_DIR)):
        return "Access Denied", 403
    
    # 기준은 BASE_DIR를 기준으로 상대 경로로 계산 (예: "word/n2")
    base = os.path.relpath(requested_path, BASE_DIR)
    
    if not os.path.isdir(requested_path):
        return "Invalid directory", 400
    
    items = os.listdir(requested_path)
    directories = []
    files = []
    for item in items:
        item_full = os.path.join(requested_path, item)
        if os.path.isdir(item_full):
            directories.append(item)
        elif os.path.isfile(item_full) and item.endswith(".txt"):
            files.append(item)
    return render_template('browse.html', base=base, directories=directories, files=files)

# 파일 선택 후 로드. gpt가 적당히 디렉터리 리스팅 막아줌.
@app.route('/load', methods=['POST'])
def load():
    selected_file = request.form.get('file')
    base = request.form.get('base', '')
    if selected_file:
        # 파일의 전체 경로 = BASE_DIR + base + selected_file
        session['FILE_PATH'] = os.path.join(BASE_DIR, base, selected_file)
        # 초기화: 기존 학습 관련 세션 데이터 삭제
        session.pop('unread_indices', None)
        session.pop('memorized_indices', None)
        session.pop('not_memorized_indices', None)
        session.pop('current_index', None)
        return redirect(url_for('main'))
    return redirect(url_for('browse', path=base))

@app.route('/main')
def main():
    lines = initialize_session()
    if len(session.get('unread_indices', [])) == 0:
        return render_template('finish.html', message="모든 단어를 학습했습니다!")
    
    if 'current_index' not in session:
        word = get_new_word()
    else:
        idx = session.get('current_index')
        word = lines[idx].strip() if idx is not None else get_new_word()

    if word is None:
        word = "모든 단어를 학습했습니다."

    progress = f"{(1 - len(session.get('unread_indices', [])) / len(lines) if lines else 0) * 100:.1f}%"
    return render_template('index.html', data=word, progress=progress)

# 확률 따라서 외운 / 못 외운 단어 재삽입함.
@app.route('/update', methods=['POST'])
def update():
    action = request.form.get('action')
    if 'current_index' not in session:
        return redirect(url_for('main'))
    idx = session.pop('current_index')
    
    if action == "not_memorized":
        not_memorized = session.get('not_memorized_indices', [])
        not_memorized.append(idx)
        session['not_memorized_indices'] = not_memorized
        if random.random() < PROB_NOT_MEMORIZED:
            unread = session.get('unread_indices', [])
            unread.append(idx)
            session['unread_indices'] = unread
    elif action == "memorized":
        memorized = session.get('memorized_indices', [])
        memorized.append(idx)
        session['memorized_indices'] = memorized
        if random.random() < PROB_MEMORIZED:
            unread = session.get('unread_indices', [])
            unread.append(idx)
            session['unread_indices'] = unread

    lines = initialize_session()
    if len(session.get('unread_indices', [])) == 0:
        return render_template('finish.html', message="모든 단어를 학습했습니다!")
    return redirect(url_for('main'))

# 세션 날리는 용
@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('root'))