# MariaDB 10.7+ 에서 Django 가 UUIDField 를 네이티브로 쓰면 INSERT 시 36자(하이픈 포함)가
# 들어갈 수 있는데, 기존 스키마는 char(32) 라서 "Data too long for column 'uuid'" 가 난다.
# MySQL 은 여전히 32자 hex 이므로 vendor 가 mysql 일 때만 넓힌다.

from django.db import migrations


def widen_uuid_for_mariadb_native(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor != "mysql":
        return
    # mysqlclient 기준 MariaDB 도 동일 backend — 네이티브 UUID 사용 시 INSERT 가 36자가 될 수 있음
    features = conn.features
    if not getattr(features, "has_native_uuid_field", False):
        return
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT COLUMN_TYPE, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'participants'
              AND COLUMN_NAME = 'uuid'
            """
        )
        row = cursor.fetchone()
        if not row:
            return
        column_type = (row[0] or "").lower()
        data_type = (row[1] or "").lower()
        # 신규 마이그레이션으로 이미 `uuid` 타입이면 변경 불필요
        if data_type == "uuid":
            return
        # char(32) 등 짧은 문자열만 넓힘 (기존 MySQL/MariaDB 스키마)
        if "char(32)" not in column_type and "varchar(32)" not in column_type:
            return
        cursor.execute(
            "ALTER TABLE `participants` MODIFY COLUMN `uuid` VARCHAR(36) NOT NULL"
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("participants", "0009_participant_product_application"),
    ]

    operations = [
        migrations.RunPython(widen_uuid_for_mariadb_native, noop_reverse),
    ]
