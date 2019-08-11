"""Task Model migrations."""


TABLE_NAME = 'estimation_summaries'


def upgrade(migrator):
    with migrator.create_table(TABLE_NAME) as table:
        table.foreign_key('uuid', 'task',
                          references='tasks.id',
                          null=False)
        table.foreign_key('uuid', 'closest_value',
                          references='estimation_values.id',
                          null=False)
        table.bool('consensus_met')
        table.decimal('average')
        table.integer('created_at')


def downgrade(migrator):
    migrator.drop_table(TABLE_NAME)
