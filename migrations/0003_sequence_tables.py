"""Sequences Model migrations."""


TABLE_NAME = 'sequences'


def upgrade(migrator):
    with migrator.create_table(TABLE_NAME) as table:
        table.char('name', max_length=255, constraints=['PRIMARY KEY'])
        table.integer('created_at')


def downgrade(migrator):
    migrator.drop_table(TABLE_NAME)
