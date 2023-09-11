import logging
import os

import click
import tqdm
from pypdf import PdfWriter

EXPORTS = "exports"
EXPORTS_PATH = None
ROOT_PATH = None
DEBUG = False

logger = logging.getLogger(__name__)


def init_log():
    global logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    # 设置日志格式
    formatter = logging.Formatter('[%(asctime)s][%(levelname)5s] %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def init():
    # 初始化日志
    init_log()

    global logger
    logger = logging.getLogger()
    logger.debug("日志配置完成")

    logger.info("初始化完成")


def main(root):
    init()

    check_root(root)

    walk(root)


def is_ignore(filename):
    if filename.startswith("."):
        return True

    return filename in {EXPORTS}


def walk(folder_path):
    all_dirs = tuple(os.listdir(folder_path))
    current = 0

    try:
        with tqdm.tqdm(total=len(all_dirs), desc="合并文件中") as pbar:
            for dirname in all_dirs:
                if is_ignore(dirname):
                    logger.debug("忽略定义的目录: %s", dirname)
                    continue

                process(dirname)

                pbar.update(1)
                current += 1
                pbar.set_description(f"处理目录{dirname}")
    except KeyboardInterrupt:
        logger.info("用户中止")
    except:
        logger.warning("处理发生未知异常", exc_info=True)

    logger.info("合并处理完成: %d/%d", current, len(all_dirs))
    logger.info("合并文件保存在目录: %s", EXPORTS_PATH)


def process(dirname):
    try:
        dir_path = os.path.join(ROOT_PATH, dirname)
        pdf_files = []
        for filename in os.listdir(dir_path):
            if not filename.endswith(".pdf"):
                logger.debug("忽略非pdf扩展名的文件: %s", filename)
                continue

            if 'binder' in filename.lower():
                logger.debug("忽略Binder文件: %s", filename)
                continue

            filepath = os.path.join(dir_path, filename)
            pdf_files.append(filepath)

        if len(pdf_files) == 0:
            logger.info("忽略空目录，目录中不包含PDF文件: %s", dir_path)
            return

        export_filename = str(os.path.join(EXPORTS_PATH, dirname + ".pdf"))
        logger.debug("准备合并PDF(%d个): %s -> %s", len(pdf_files), dir_path, export_filename)

        if os.path.exists(export_filename):
            os.remove(export_filename)

        merger = PdfWriter()
        for pdf in sorted(pdf_files):
            merger.append(pdf)

        merger.write(export_filename)
        merger.close()
        logger.debug("成功合并PDF: %s", export_filename)
    except KeyboardInterrupt as e:
        raise e
    except:
        logger.warning("合并PDF失败: %s", dirname)
        logger.debug("合并PDF失败详细: %s", dirname, exc_info=True)


def check_root(root):
    global EXPORTS_PATH, ROOT_PATH

    ROOT_PATH = os.path.abspath(root)
    logger.info("PDF文件目录: %s", ROOT_PATH)

    EXPORTS_PATH = os.path.join(ROOT_PATH, EXPORTS)

    try:
        if not os.path.exists(EXPORTS_PATH):
            os.makedirs(EXPORTS_PATH)
            logger.debug("导出目录自动创建: %s", EXPORTS_PATH)
    except:
        logger.error("导出目录无法创建。可能因为权限问题。请使用管理员模式打开命令行或将PDF目录放到当前用户目录")


@click.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--v', is_flag=True, help='在控制台输出调试信息')
def cli(file_path, v=False):
    """
    简单合并PDF工具。以目录为单位合并文件，合并结果存放在顶层目录下的exports目录中。
    目录内PDF文件将按照目录名顺序合并。

    参数:
        file_path : 所有PDF（以目录为单位）的最上级目录，合并结果存放在[file_path]/exports目录下

    示例:
        python main.py /Users/wangs/Downloads/
    """

    if v:
        global DEBUG
        DEBUG = True

    main(file_path)


def mock(root, dirname):
    import shutil
    template = os.path.join(root, dirname)

    for i in range(10000):
        destination_directory = os.path.join(root, dirname + "#" + str(i + 1))
        shutil.copytree(template, destination_directory)


if __name__ == '__main__':
    cli()
    # mock("/Users/wangs/tmp/测试/", "/Users/wangs/tmp/测试/2021024236-302#")
