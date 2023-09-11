import csv
import logging
import os
import tempfile
from collections import OrderedDict

import cv2
import tqdm
from pypdf import PdfReader

logger = logging.getLogger(__name__)


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

    try:
        with tqdm.tqdm(total=len(what), desc="检测文件") as pbar:
            for filename in what:
                result = detect_blur_pdf(filename)
                if result is not None:
                    scores.update({filename: result})

                pbar.update(1)
                current += 1
                pbar.set_description(f"检测文件{filename}")
    except KeyboardInterrupt:
        logger.info("用户中止")
    except:
        logger.warning("处理发生未知异常", exc_info=True)

    export_file = exports(root_path, scores.items())
    logger.info("检测完成：共%d个文件 -> %s", len(what), export_file)


def exports(root, data):
    export_file = tempfile.mktemp(".xls", prefix="export_", dir=root)
    with open(export_file, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        for row in data:
            csv_writer.writerow(row)

    return export_file


def detect_blur_pdf(file_name):
    reader = PdfReader(file_name)

    page = reader.pages[0]
    import tempfile
    image_file_object = page.images[0]

    with tempfile.NamedTemporaryFile() as fp:
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


# @click.command()
# @click.argument('file_path', type=click.Path(exists=True))
# @click.option('--v', is_flag=True, help='在控制台输出调试信息')
def cli(file_path, v=True):
    """
    简单合并PDF工具。以目录为单位合并文件，合并结果存放在顶层目录下的exports目录中。
    目录内PDF文件将按照目录名顺序合并。

    参数:
        file_path : 所有PDF（以目录为单位）的最上级目录，合并结果存放在[file_path]/exports目录下

    示例:
        python check.py /Users/wangs/Downloads/
    """

    if v:
        global DEBUG
        DEBUG = True

        # 初始化日志
    from app.main import init_log
    init_log()

    global logger
    logger = logging.getLogger()
    logger.debug("日志配置完成")

    walk_blur(file_path)


if __name__ == "__main__":
    cli("/Users/wangs/tmp/sample")
