"""User Model migrations."""


def upgrade(migrator):
    with migrator.create_table('users') as table:
        table.uuid('id', constraints=['PRIMARY KEY'])
        table.integer('registered_on')
        table.char('email', max_length=255)
        table.char('name', max_length=255)
        table.char('role', max_length=128)
        table.char('password', max_length=255)
        table.foreign_key('uuid', 'organization_id',
                          references='organizations.id',
                          null=True)


def downgrade(migrator):
    migrator.drop_table('users')
