开发环境(基于 python3):

1. 安装虚拟环境, 切换到根目录执行: virtualenv venv
2. 进入虚拟环境: . venv/bin/activate
3. 首次需要安装 mysql 连接 c 库:
    1. 安装 Homebrew
    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    2. 安装 mysql-connector-c
    brew install mysql-connector-c
4. 安装依赖: pip install -r requirements/development.txt
5. 生成依赖: pip freeze > requirements/development.txt
6. 数据库版本迁移
    a. 初始化 alembic init migrations
       注释掉 alembic.ini 文件 sqlalchemy.url
       migrations/env.py  target_metadata 引入
            import os
            import sys

            # 将当前目录(项目更目录)加入sys.path, 当然也可以将根目录下的model加入sys.path,这样就不需要将model封装成模块
            sys.path.append(os.getcwd())
            from app.model import *
            config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
            target_metadata = Base.metadata
    b. 生成版本文件     alembic revision --autogenerate
    c. 更新版本文件     alembic upgrade head
    d. 第一次导入使用手动逐条导入
                         alembic --config ./alembic.ini history
                         alembic upgrade 050
7.允许后台脚本例子

      export PYTHONPATH=$(pwd)
      python app/engine/engine.py