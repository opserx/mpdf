import csv
import logging
import os
import shutil
import tempfile
from collections import OrderedDict

import click
import cv2
import tqdm
from pypdf import PdfReader

logger = logging.getLogger(__name__)

DEBUG = False

import logging


def init_log(is_debug=False):
    global logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if is_debug else logging.INFO)

    # 设置日志格式
    formatter = logging.Formatter('[%(asctime)s][%(levelname)5s] %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def walk_blur(root_path):
    logger.info("待检测文件信息搜索中...")
    what = []
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if not file.lower().endswith((".pdf",)):
                logger.debug("跳过非PDF文件: %s", file)
                continue

            what.append(os.path.join(root, file))

    logger.info("共发现%d个待检测文件", len(what))

    current = 0

    scores = OrderedDict()
    tmp_root = os.path.join(root_path, "tmp")
    logger.info("创建临时目录: %s", tmp_root)
    os.makedirs(tmp_root, exist_ok=True)

    try:
        with tqdm.tqdm(total=len(what), desc="检测文件") as pbar:
            for filename in what:
                try:
                    result = detect_blur_pdf(filename, tmp_root)
                    if result is not None:
                        scores.update({filename: result})
                    else:
                        logger.debug("无法检测文件: %s", filename)
                except:
                    logger.warning("检测文件失败: %s", filename)

                pbar.update(1)
                current += 1
                sname = os.path.basename(filename)
                pbar.set_description(f"检测文件{sname}")
    except KeyboardInterrupt:
        logger.info("用户中止")
    except:
        logger.warning("处理发生未知异常", exc_info=True)

    export_file = exports(root_path, scores.items())

    try:
        shutil.rmtree(tmp_root)
        logger.info("删除临时目录: %s", tmp_root)
    except:
        logger.warning("删除临时目录失败: %s", tmp_root)

    logger.info("检测完成：共%d个文件 -> %s", len(what), export_file)


def exports(root, data):
    export_file = tempfile.mktemp(".xls", prefix="export_", dir=root)
    with open(export_file, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        for row in data:
            csv_writer.writerow(row)

    return export_file


def detect_blur_pdf(file_name, tmp_root):
    reader = PdfReader(file_name)

    page = reader.pages[0]
    import tempfile
    image_file_object = page.images[0]

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=tmp_root) as fp:
        fp.write(image_file_object.data)
        temp_file_name = fp.name
        return detect_blur(temp_file_name)


def detect_blur(image_path):
    try:
        # 读取图像
        image = cv2.imread(image_path)

        # 转换为灰度图像
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 计算图像的模糊程度
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

        return blur_score
    except:
        logger.debug("检测失败: %s", image_path, exc_info=True)
        return None


@click.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--v', is_flag=True, help='在控制台输出调试信息')
def cli(file_path, v=True):
    """
    检测PDF中的图片模糊度，结果保存到excel文件中。

    参数:
        file_path : 包含PDF的目录，支持多级目录嵌套

    示例:
        python check.py /Users/wangs/Downloads/
    """
    # 初始化日志

    global DEBUG

    if v:
        DEBUG = True

    init_log(is_debug=DEBUG)

    global logger
    logger = logging.getLogger()
    logger.debug("日志配置完成")

    walk_blur(file_path)


if __name__ == "__main__":
    cli()
