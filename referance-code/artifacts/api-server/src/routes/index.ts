import { Router, type IRouter } from "express";
import healthRouter from "./health";
import authRouter from "./auth";
import usersRouter from "./users";
import propertiesRouter from "./properties";
import unitsRouter from "./units";
import tenantsRouter from "./tenants";
import leasesRouter from "./leases";
import financeRouter from "./finance";
import maintenanceRouter from "./maintenance";
import dashboardRouter from "./dashboard";

const router: IRouter = Router();

router.use(healthRouter);
router.use(authRouter);
router.use(usersRouter);
router.use(propertiesRouter);
router.use(unitsRouter);
router.use(tenantsRouter);
router.use(leasesRouter);
router.use(financeRouter);
router.use(maintenanceRouter);
router.use(dashboardRouter);

export default router;
