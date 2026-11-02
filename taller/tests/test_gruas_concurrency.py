"""PostgreSQL-only concurrency checks for towing reservations.

Run with a dedicated test settings module pointing at an isolated PostgreSQL
database.  These tests deliberately skip SQLite: its locking semantics do not
prove the production guarantee.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import connection, close_old_connections, transaction
from django.test import TransactionTestCase
from django.utils import timezone

from taller.gruas.services.assignment_service import assign_order
from taller.gruas.services.order_service import accept_quote, create_quote
from taller.models import Empresa, TowingAssignment, TowingDriver, TowingOrder, TowingUnit


@skipUnless(connection.vendor == "postgresql", "La concurrencia debe validarse en PostgreSQL aislado")
class TowingConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("pg-owner", password="x")
        self.empresa = Empresa.objects.create(user=self.user, nombre_taller="PG Towing", pais="CL", moneda="CLP")
        self.unit = TowingUnit.objects.create(empresa=self.empresa, nombre="P1", patente="PG-001")
        self.driver = TowingDriver.objects.create(empresa=self.empresa, nombre="D1")

    def _accepted_order(self, numero):
        order = TowingOrder.objects.create(empresa=self.empresa, numero=numero, origen="A", destino="B")
        quote = create_quote(order_id=order.id, empresa=self.empresa, user=self.user, net_amount=Decimal("100"), tax_rate=Decimal("0"))
        accept_quote(quote_id=quote.id, empresa=self.empresa, user=self.user)
        return order

    def _race(self, unit_id, driver_id, start, end):
        orders = [self._accepted_order("PG-RACE-1"), self._accepted_order("PG-RACE-2")]
        barrier = Barrier(2)

        def worker(order):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                with transaction.atomic():
                    return assign_order(order_id=order.id, empresa=self.empresa, unit_id=unit_id, driver_id=driver_id, planned_start_at=start, planned_end_at=end, user=self.user).id
            except Exception as exc:  # one contender must lose with a validation/serialization error
                return exc
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, orders))
        return results

    def test_same_unit_simultaneous_reservation_only_one_commits(self):
        start = timezone.now() + timedelta(hours=1)
        results = self._race(self.unit.id, self.driver.id, start, start + timedelta(hours=2))
        # The resource lock permits exactly one competing order to commit.
        self.assertEqual(sum(isinstance(result, int) for result in results), 1)
        self.assertEqual(TowingUnit.objects.get(pk=self.unit.id).assignments.filter(is_active=True).count(), 1)

    def test_contiguous_reservations_are_allowed(self):
        first = self._accepted_order("PG-CONTIG-1")
        second = self._accepted_order("PG-CONTIG-2")
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)
        assign_order(order_id=first.id, empresa=self.empresa, unit_id=self.unit.id, driver_id=self.driver.id, planned_start_at=start, planned_end_at=end, user=self.user)
        # A contiguous interval on the *same* resources is not an overlap.
        assign_order(order_id=second.id, empresa=self.empresa, unit_id=self.unit.id, driver_id=self.driver.id, planned_start_at=end, planned_end_at=end + timedelta(hours=1), user=self.user)
        self.assertEqual(TowingOrder.objects.filter(status=TowingOrder.STATUS_ASSIGNED).count(), 2)

    def test_overlapping_reservations_same_driver_different_units_are_rejected(self):
        unit2 = TowingUnit.objects.create(empresa=self.empresa, nombre="P2", patente="PG-002")
        first = self._accepted_order("PG-DRIVER-OVERLAP-1")
        second = self._accepted_order("PG-DRIVER-OVERLAP-2")
        start = timezone.now() + timedelta(hours=2)
        assign_order(
            order_id=first.id, empresa=self.empresa, unit_id=self.unit.id,
            driver_id=self.driver.id, planned_start_at=start,
            planned_end_at=start + timedelta(hours=2), user=self.user,
        )
        with self.assertRaises(Exception):
            assign_order(
                order_id=second.id, empresa=self.empresa, unit_id=unit2.id,
                driver_id=self.driver.id, planned_start_at=start + timedelta(minutes=1),
                planned_end_at=start + timedelta(hours=1), user=self.user,
            )

    def test_same_driver_with_different_units_cannot_overlap(self):
        unit2 = TowingUnit.objects.create(empresa=self.empresa, nombre="P2", patente="PG-002")
        orders = [self._accepted_order("PG-DRIVER-1"), self._accepted_order("PG-DRIVER-2")]
        start = timezone.now() + timedelta(hours=2)
        assign_order(order_id=orders[0].id, empresa=self.empresa, unit_id=self.unit.id, driver_id=self.driver.id, planned_start_at=start, planned_end_at=start + timedelta(hours=2), user=self.user)
        with self.assertRaises(Exception):
            assign_order(order_id=orders[1].id, empresa=self.empresa, unit_id=unit2.id, driver_id=self.driver.id, planned_start_at=start + timedelta(minutes=1), planned_end_at=start + timedelta(hours=1), user=self.user)

    def test_delayed_active_service_blocks_new_start_until_released(self):
        first = self._accepted_order("PG-DELAY-1")
        second = self._accepted_order("PG-DELAY-2")
        start = timezone.now() - timedelta(minutes=30)
        end = timezone.now() + timedelta(hours=1)
        assign_order(order_id=first.id, empresa=self.empresa, unit_id=self.unit.id, driver_id=self.driver.id, planned_start_at=start, planned_end_at=end, user=self.user)
        with self.assertRaises(Exception):
            assign_order(order_id=second.id, empresa=self.empresa, unit_id=self.unit.id, driver_id=self.driver.id, planned_start_at=timezone.now(), planned_end_at=timezone.now() + timedelta(minutes=30), user=self.user)

    def test_failed_reassignment_keeps_previous_assignment(self):
        order = self._accepted_order("PG-ROLLBACK")
        start = timezone.now() + timedelta(hours=1)
        previous = assign_order(order_id=order.id, empresa=self.empresa, unit_id=self.unit.id, driver_id=self.driver.id, planned_start_at=start, planned_end_at=start + timedelta(hours=1), user=self.user)
        with self.assertRaises(Exception):
            assign_order(order_id=order.id, empresa=self.empresa, unit_id=999999, driver_id=self.driver.id, planned_start_at=start, planned_end_at=start + timedelta(hours=1), user=self.user)
        previous.refresh_from_db()
        self.assertTrue(previous.is_active)

    def test_two_simultaneous_reassignments_same_order_leave_one_active(self):
        order = self._accepted_order("PG-REASSIGN-RACE")
        unit2 = TowingUnit.objects.create(empresa=self.empresa, nombre="P2", patente="PG-002")
        driver2 = TowingDriver.objects.create(empresa=self.empresa, nombre="D2")
        start = timezone.now() + timedelta(hours=1)
        initial = assign_order(
            order_id=order.id, empresa=self.empresa, unit_id=self.unit.id,
            driver_id=self.driver.id, planned_start_at=start,
            planned_end_at=start + timedelta(hours=1), user=self.user,
        )
        barrier = Barrier(2)

        def worker(unit_id, driver_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                with transaction.atomic():
                    return assign_order(
                        order_id=order.id, empresa=self.empresa, unit_id=unit_id,
                        driver_id=driver_id, planned_start_at=start,
                        planned_end_at=start + timedelta(hours=1), user=self.user,
                    ).id
            except Exception as exc:
                return exc
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, (self.unit.id, unit2.id), (self.driver.id, driver2.id)))

        order.refresh_from_db()
        active = list(order.assignments.filter(is_active=True))
        self.assertEqual(len(active), 1)
        initial.refresh_from_db()
        self.assertFalse(initial.is_active)
        # Both requests may serialize successfully; the invariant is that only
        # the last committed assignment remains active for the order.
        self.assertEqual(sum(isinstance(result, int) for result in results), 2)

    def test_simultaneous_different_orders_competing_for_same_resources(self):
        results = self._race(
            self.unit.id,
            self.driver.id,
            timezone.now() + timedelta(hours=3),
            timezone.now() + timedelta(hours=5),
        )
        self.assertEqual(sum(isinstance(result, int) for result in results), 1)
        self.assertEqual(
            TowingAssignment.objects.filter(unit=self.unit, driver=self.driver, is_active=True).count(),
            1,
        )
