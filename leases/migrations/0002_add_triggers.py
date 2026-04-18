"""
leases/migrations/0002_add_triggers.py
Adds the two MySQL BEFORE INSERT / BEFORE UPDATE triggers that enforce
the "one active lease per unit" rule at the database level.
These supplement the application-layer check in leases/models.py clean().
"""
from django.db import migrations


INSERT_TRIGGER_SQL = """
CREATE TRIGGER trg_one_active_lease_per_unit_insert
BEFORE INSERT ON leases_lease
FOR EACH ROW
BEGIN
  IF NEW.is_active = 1 THEN
    IF (
      SELECT COUNT(*)
      FROM leases_lease
      WHERE unit_id = NEW.unit_id
        AND is_active = 1
    ) > 0 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
          'Cannot create lease: this unit already has an active lease. Terminate the existing lease before creating a new one.';
    END IF;
  END IF;
END
"""

UPDATE_TRIGGER_SQL = """
CREATE TRIGGER trg_one_active_lease_per_unit_update
BEFORE UPDATE ON leases_lease
FOR EACH ROW
BEGIN
  IF NEW.is_active = 1 AND OLD.is_active = 0 THEN
    IF (
      SELECT COUNT(*)
      FROM leases_lease
      WHERE unit_id = NEW.unit_id
        AND is_active = 1
        AND id != NEW.id
    ) > 0 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
          'Cannot reactivate lease: this unit already has an active lease.';
    END IF;
  END IF;
END
"""

DROP_INSERT_TRIGGER = "DROP TRIGGER IF EXISTS trg_one_active_lease_per_unit_insert;"
DROP_UPDATE_TRIGGER = "DROP TRIGGER IF EXISTS trg_one_active_lease_per_unit_update;"


class Migration(migrations.Migration):

    dependencies = [
        ('leases', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=INSERT_TRIGGER_SQL,
            reverse_sql=DROP_INSERT_TRIGGER,
        ),
        migrations.RunSQL(
            sql=UPDATE_TRIGGER_SQL,
            reverse_sql=DROP_UPDATE_TRIGGER,
        ),
    ]
