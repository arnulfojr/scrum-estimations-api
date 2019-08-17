"""Session Model migrations."""


TABLE_NAME = 'sessions'


def upgrade(migrator):
    with migrator.create_table(TABLE_NAME) as table:
        table.uuid('id', constraints=['PRIMARY KEY'])
        table.char('name', null=True, max_length=255)
        table.foreign_key('uuid', 'organization_id',
                          references=f'organizations.id',
                          on_delete='CASCADE',
                          null=False)
        table.foreign_key('char', 'sequence',
                          references='sequences.name',
                          null=False)
        table.bool('completed', null=False)
        table.integer('completed_at', null=True)
        table.integer('created_at')


def downgrade(migrator):
    migrator.drop_table(TABLE_NAME)
