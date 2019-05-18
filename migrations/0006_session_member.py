"""Session-Memeber Model migrations."""


TABLE_NAME = 'session_members'


def upgrade(migrator):
    with migrator.create_table(TABLE_NAME) as table:
        table.foreign_key('uuid', 'user',
                          references='users.id',
                          null=False)
        table.foreign_key('uuid', 'session',
                          references='sessions.id',
                          null=False)
        table.add_index(('user', 'session'), unique=True)


def downgrade(migrator):
    migrator.drop_table(TABLE_NAME)
