"""Task Model migrations."""


TABLE_NAME = 'tasks'


def upgrade(migrator):
    with migrator.create_table(TABLE_NAME) as table:
        table.uuid('id', constraints=['PRIMARY KEY'])
        table.char('name', null=True, max_length=255)
        table.add_index(('name',), unique=False)

        table.foreign_key('char', 'session',
                          references='sessions.id',
                          null=False)
        table.integer('created_at')


def downgrade(migrator):
    migrator.drop_table(TABLE_NAME)
