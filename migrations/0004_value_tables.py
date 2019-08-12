"""Estimation Values Model migrations."""


TABLE_NAME = 'estimation_values'


def upgrade(migrator):
    with migrator.create_table(TABLE_NAME) as table:
        table.uuid('id', constraints=['PRIMARY KEY'])
        table.foreign_key('char', 'sequence',
                          references='sequences.name',
                          null=False)
        table.foreign_key('uuid', 'previous',
                          references=f'{TABLE_NAME}.id',
                          null=True)
        table.foreign_key('uuid', 'next',
                          references=f'{TABLE_NAME}.id',
                          null=True)
        table.char('name', null=True, max_length=255)
        table.decimal('value', null=True)
        table.integer('created_at')


def downgrade(migrator):
    migrator.drop_table(TABLE_NAME)
