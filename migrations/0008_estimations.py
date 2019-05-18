"""Task Model migrations."""


TABLE_NAME = 'estimations'


def upgrade(migrator):
    with migrator.create_table(TABLE_NAME) as table:
        table.uuid('id', constraints=['PRIMARY KEY'])
        table.foreign_key('uuid', 'task',
                          references='tasks.id',
                          null=False)
        table.foreign_key('uuid', 'user',
                          references='users.id',
                          null=False)
        table.foreign_key('uuid', 'value',
                          references='estimation_values.id',
                          null=False)
        table.add_index(('task', 'user'), unique=False)
        table.integer('created_at')


def downgrade(migrator):
    migrator.drop_table(TABLE_NAME)
