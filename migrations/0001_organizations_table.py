"""Organization's Model migrations."""


def upgrade(migrator):
    with migrator.create_table('organizations') as table:
        table.uuid('id', constraints=['PRIMARY KEY'])
        table.integer('registered_on')
        table.char('name', max_length=255)


def downgrade(migrator):
    migrator.drop_table('organizations')
