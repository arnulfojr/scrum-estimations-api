"""Task Model migrations."""
from peewee_moves import Migrator


TABLE_NAME = 'estimations'


def upgrade(migrator: Migrator):
    with migrator.create_table(TABLE_NAME) as table:
        table.uuid('id', constraints=['PRIMARY KEY'])
        table.foreign_key('uuid', 'task',
                          references='tasks.id',
                          on_delete='CASCADE',
                          null=False)
        table.foreign_key('uuid', 'value',
                          references='estimation_values.id',
                          on_delete='CASCADE',
                          null=False)
        table.foreign_key('uuid', 'user',
                          references='users.id',
                          on_delete='CASCADE',
                          null=False)
        table.integer('created_at')


def downgrade(migrator: Migrator):
    migrator.drop_table(TABLE_NAME)
