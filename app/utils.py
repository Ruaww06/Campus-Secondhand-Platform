import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename):
    """校验文件后缀是否允许上传。"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_upload_file(file, subdir):
    """
    通用文件上传函数。
    subdir: 如 'goods', 'avatars'
    保存到 static/uploads/<subdir>/<uuid>.<ext>
    返回: 相对路径字符串，如 '/static/uploads/goods/abc123.jpg'
    """
    if not allowed_file(file.filename):
        raise ValueError('不支持的文件类型')

    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subdir)
    os.makedirs(upload_dir, exist_ok=True)

    abs_path = os.path.join(upload_dir, filename)
    file.save(abs_path)

    rel_path = f"/static/uploads/{subdir}/{filename}"
    return rel_path


def delete_upload_file(file_path):
    """删除物理文件。file_path 为相对路径如 /static/uploads/goods/xxx.jpg"""
    if not file_path:
        return
    abs_path = os.path.join(current_app.root_path, file_path.lstrip('/'))
    if os.path.exists(abs_path):
        os.remove(abs_path)


def save_goods_images(files, goods_id):
    """
    保存商品图片（内部调用 save_upload_file）。
    第一张设为主图。
    返回相对路径列表。
    """
    from app.models import GoodsImage, db

    paths = []
    subdir = f"goods_{goods_id}"
    for idx, file in enumerate(files):
        if file and file.filename:
            path = save_upload_file(file, subdir)
            paths.append(path)
    return paths
