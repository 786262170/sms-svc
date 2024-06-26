"""empty message

Revision ID: 52d0f2f38bf0
Revises: 
Create Date: 2022-08-19 14:43:27.690527

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '52d0f2f38bf0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin_user',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('uid', sa.String(length=20), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=True),
    sa.Column('password', sa.String(length=256), nullable=False),
    sa.Column('security_password', sa.String(length=256), nullable=True),
    sa.Column('role', sa.SmallInteger(), nullable=False),
    sa.Column('locked', sa.SmallInteger(), nullable=False),
    sa.Column('active', sa.SmallInteger(), nullable=False),
    sa.Column('token', sa.String(length=256), nullable=True),
    sa.Column('permission', sa.Text(), nullable=True),
    sa.Column('parent_id', sa.String(length=36), nullable=True),
    sa.Column('email', sa.String(length=50), nullable=True),
    sa.Column('avatar', sa.String(length=128), nullable=True),
    sa.Column('name', sa.String(length=60), nullable=True),
    sa.Column('country_code', sa.String(length=16), nullable=True),
    sa.Column('mobile', sa.String(length=16), nullable=True),
    sa.Column('balance', sa.Numeric(precision=24, scale=8), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['admin_user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('mobile'),
    sa.UniqueConstraint('uid')
    )
    op.create_table('captcha_pin_code',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('pin_code_signature', sa.String(length=256), nullable=False),
    sa.Column('try_times', sa.SmallInteger(), nullable=True),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('daily_schedule_task',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=True),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.Column('timestamp', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('timestamp')
    )
    op.create_table('email_pin_code',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('pin_code_signature', sa.String(length=256), nullable=False),
    sa.Column('try_times', sa.SmallInteger(), nullable=True),
    sa.Column('id', sa.String(length=60), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('setting',
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('name')
    )
    op.create_table('sms_channel',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('name', sa.String(length=36), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('provider', sa.Integer(), nullable=False),
    sa.Column('app_id', sa.String(length=36), nullable=False),
    sa.Column('app_key', sa.String(length=128), nullable=False),
    sa.PrimaryKeyConstraint('name')
    )
    op.create_table('sms_pin_code',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('pin_code_signature', sa.String(length=256), nullable=False),
    sa.Column('try_times', sa.SmallInteger(), nullable=True),
    sa.Column('id', sa.String(length=11), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('admin_register_schedule_task',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=True),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.Column('admin_user_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['admin_user_id'], ['admin_user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('admin_user_id')
    )
    op.create_table('sms_product',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('channel_name', sa.String(length=36), nullable=False),
    sa.Column('admin_user_id', sa.String(length=36), nullable=False),
    sa.Column('country', sa.String(length=36), nullable=False, comment='国家'),
    sa.Column('country_code', sa.Integer(), nullable=False, comment='手机国家码'),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('provider', sa.Integer(), nullable=False),
    sa.Column('channel_price', sa.Numeric(precision=24, scale=8), nullable=False, comment='通道价格'),
    sa.Column('price', sa.Numeric(precision=24, scale=8), nullable=False, comment='默认价格'),
    sa.Column('cost_price', sa.Numeric(precision=24, scale=8), nullable=False, comment='成本价格'),
    sa.Column('list_price', sa.Numeric(precision=24, scale=8), nullable=False, comment='通道最高价格'),
    sa.Column('invalid', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['admin_user_id'], ['admin_user.id'], ),
    sa.ForeignKeyConstraint(['channel_name'], ['sms_channel.name'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('admin_user_id', 'country', 'channel_name')
    )
    op.create_table('sms_special_check',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('channel_name', sa.String(length=36), nullable=False),
    sa.Column('page_size', sa.SmallInteger(), nullable=False),
    sa.Column('num', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['channel_name'], ['sms_channel.name'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sms_special_not_found_record',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('channel_name', sa.String(length=36), nullable=False),
    sa.Column('num', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('info', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['channel_name'], ['sms_channel.name'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('channel_name', 'num', 'date')
    )
    op.create_table('user',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('uid', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=50), nullable=False),
    sa.Column('country_code', sa.String(length=16), nullable=True),
    sa.Column('mobile', sa.String(length=16), nullable=True),
    sa.Column('password', sa.String(length=256), nullable=False),
    sa.Column('security_password', sa.String(length=256), nullable=True),
    sa.Column('locked', sa.SmallInteger(), nullable=False),
    sa.Column('active', sa.SmallInteger(), nullable=False),
    sa.Column('token', sa.String(length=256), nullable=True),
    sa.Column('admin_user_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=True),
    sa.Column('first_name', sa.String(length=60), nullable=True),
    sa.Column('last_name', sa.String(length=60), nullable=True),
    sa.Column('nickname', sa.String(length=60), nullable=True),
    sa.Column('avatar', sa.String(length=256), nullable=True),
    sa.Column('status_2FA', sa.SmallInteger(), nullable=False),
    sa.Column('usdt_number', sa.String(length=16), nullable=True),
    sa.Column('usdt_address', sa.String(length=128), nullable=True),
    sa.Column('usdt_recharge', sa.Numeric(precision=24, scale=8), nullable=True),
    sa.Column('usdt_balance', sa.Numeric(precision=24, scale=8), nullable=True),
    sa.Column('balance', sa.Numeric(precision=24, scale=2), nullable=True),
    sa.Column('frozen_balance', sa.Numeric(precision=24, scale=8), nullable=True),
    sa.Column('default_sms_channel_name', sa.String(length=50), nullable=True),
    sa.Column('default_verify_channel_name', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['admin_user_id'], ['admin_user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('uid'),
    sa.UniqueConstraint('usdt_address'),
    sa.UniqueConstraint('usdt_number')
    )
    op.create_table('application',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('app_id', sa.String(length=18), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=False),
    sa.Column('app_key', sa.String(length=128), nullable=False),
    sa.Column('sms_hook_url', sa.String(length=256), nullable=True),
    sa.Column('invalid', sa.Integer(), nullable=False),
    sa.Column('country', sa.String(length=60), nullable=True),
    sa.Column('link', sa.String(length=200), nullable=True),
    sa.Column('remark', sa.String(length=200), nullable=True),
    sa.Column('category', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('app_id')
    )
    op.create_table('contact_group',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'name')
    )
    op.create_table('message_template',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('shared', sa.SmallInteger(), nullable=True),
    sa.Column('tags', sa.Integer(), nullable=True),
    sa.Column('interests', sa.Integer(), nullable=True),
    sa.Column('status', sa.Integer(), nullable=False),
    sa.Column('invalid', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sms_user',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('channel_name', sa.String(length=36), nullable=False),
    sa.Column('country', sa.String(length=36), nullable=False, comment='国家'),
    sa.Column('country_code', sa.Integer(), nullable=False, comment='手机国家码'),
    sa.Column('provider', sa.Integer(), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('price', sa.Numeric(precision=24, scale=8), nullable=False, comment='价格'),
    sa.Column('default_price', sa.Numeric(precision=24, scale=8), nullable=False, comment='价格'),
    sa.ForeignKeyConstraint(['channel_name'], ['sms_channel.name'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'country', 'channel_name')
    )
    op.create_table('user_balance_record',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('other_user_id', sa.String(length=36), nullable=True),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('record_type', sa.Integer(), nullable=False),
    sa.Column('current_amount', sa.Numeric(precision=24, scale=8), nullable=False),
    sa.Column('delta_amount', sa.Numeric(precision=24, scale=8), nullable=False),
    sa.Column('details', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['other_user_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_login_record',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('login_status', sa.SmallInteger(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_register_schedule_task',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=True),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('wallet_order',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('amount', sa.Numeric(precision=24, scale=8), nullable=False),
    sa.Column('payment_type', sa.SmallInteger(), nullable=False),
    sa.Column('card_number', sa.String(length=64), nullable=True),
    sa.Column('wechat', sa.String(length=64), nullable=True),
    sa.Column('alipay', sa.String(length=64), nullable=True),
    sa.Column('address', sa.String(length=64), nullable=True),
    sa.Column('image', sa.String(length=512), nullable=True),
    sa.Column('remark', sa.String(length=64), nullable=True),
    sa.Column('status', sa.SmallInteger(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('contact',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('first_name', sa.String(length=60), nullable=True),
    sa.Column('last_name', sa.String(length=60), nullable=True),
    sa.Column('gender', sa.Integer(), nullable=True),
    sa.Column('country', sa.String(length=60), nullable=True),
    sa.Column('mobile', sa.String(length=16), nullable=False),
    sa.Column('email', sa.String(length=64), nullable=True),
    sa.Column('title', sa.String(length=128), nullable=True),
    sa.Column('company', sa.String(length=128), nullable=True),
    sa.Column('custom_json', sa.Text(), nullable=True),
    sa.Column('blacklisted', sa.String(length=16), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['contact_group.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('message',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('app_id', sa.String(length=18), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.Column('mobile', sa.Text(length=10000000), nullable=False),
    sa.Column('filtered_mobile', sa.Text(length=10000000), nullable=True),
    sa.Column('type', sa.SmallInteger(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=True),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['app_id'], ['application.app_id'], ),
    sa.ForeignKeyConstraint(['group_id'], ['contact_group.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('message_timing',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('app_id', sa.String(length=18), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.Column('mobile', sa.Text(), nullable=False),
    sa.Column('mobile_count', sa.Integer(), nullable=False),
    sa.Column('filtered_mobile', sa.Text(), nullable=True),
    sa.Column('filtered_mobile_count', sa.Integer(), nullable=True),
    sa.Column('delivered_count', sa.Integer(), nullable=False),
    sa.Column('type', sa.SmallInteger(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('timing_at', sa.DateTime(), nullable=False),
    sa.Column('frequency', sa.SmallInteger(), nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=True),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.Column('invalid', sa.SmallInteger(), nullable=False),
    sa.ForeignKeyConstraint(['app_id'], ['application.app_id'], ),
    sa.ForeignKeyConstraint(['group_id'], ['contact_group.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('message_check',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('message_id', sa.String(length=36), nullable=True),
    sa.Column('message_timing_id', sa.String(length=36), nullable=True),
    sa.Column('sms_product_id', sa.String(length=36), nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=True),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.Column('country', sa.String(length=36), nullable=False, comment='国家'),
    sa.Column('phone_number', sa.String(length=36), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('message_number', sa.String(length=36), nullable=True, comment='sms发送后返回的number'),
    sa.Column('message_status', sa.Integer(), nullable=False),
    sa.Column('price', sa.Numeric(precision=24, scale=8), nullable=False),
    sa.ForeignKeyConstraint(['message_id'], ['message.id'], ),
    sa.ForeignKeyConstraint(['message_timing_id'], ['message_timing.id'], ),
    sa.ForeignKeyConstraint(['sms_product_id'], ['sms_product.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('admin_user_balance_record',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('admin_id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('sms_check_id', sa.Integer(), nullable=True),
    sa.Column('record_type', sa.Integer(), nullable=False),
    sa.Column('current_amount', sa.Numeric(precision=24, scale=8), nullable=False),
    sa.Column('delta_amount', sa.Numeric(precision=24, scale=8), nullable=False),
    sa.Column('details', sa.Text(), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['admin_id'], ['admin_user.id'], ),
    sa.ForeignKeyConstraint(['sms_check_id'], ['message_check.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('admin_user_balance_record')
    op.drop_table('message_check')
    op.drop_table('message_timing')
    op.drop_table('message')
    op.drop_table('contact')
    op.drop_table('wallet_order')
    op.drop_table('user_register_schedule_task')
    op.drop_table('user_login_record')
    op.drop_table('user_balance_record')
    op.drop_table('sms_user')
    op.drop_table('message_template')
    op.drop_table('contact_group')
    op.drop_table('application')
    op.drop_table('user')
    op.drop_table('sms_special_not_found_record')
    op.drop_table('sms_special_check')
    op.drop_table('sms_product')
    op.drop_table('admin_register_schedule_task')
    op.drop_table('sms_pin_code')
    op.drop_table('sms_channel')
    op.drop_table('setting')
    op.drop_table('email_pin_code')
    op.drop_table('daily_schedule_task')
    op.drop_table('captcha_pin_code')
    op.drop_table('admin_user')
    # ### end Alembic commands ###
