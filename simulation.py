import sys
import math

from wave_attenuation_1d import cli, solver as s
from pathlib import Path
from dataclasses import dataclass
from configparser import ConfigParser


@dataclass
class MangroveConfig:
    """
    Class for storing mangrove specie configurations. \n
    Holds their scientific name, bulk drag coeffiecient, root density, root diameter
    and root height. \n
    All except for name are stored as ranges, implemented as tuples with two values.
    """
    sp_name: str
    bulk_drag_c: tuple[float]
    r_density: tuple[float]
    r_diameter: tuple[float]
    r_height: tuple[float]

@dataclass
class ScenarioConfig:
    """Scenario configuration parameters with physical units"""
    # Domain parameters
    L: float          # Domain length [m]
    d: float          # Water depth [m]
    dx: float         # Spatial discretization [m]
    T: float          # Total simulation time [s]
    
    # Wave parameters
    A: float          # Wave amplitude [m]
    omega: float      # Angular frequency [rad/s]
    
    # Vegetation parameters
    veg_start: float  # Vegetation zone start [m]
    veg_end: float    # Vegetation zone end [m]
    veg_density: str  # Vegetation density, either sparse, average, dense
    
    # Numerical parameters
    cfl_target: float # Target CFL number (Courant-Friedrichs-Lewy)
    output_dt: float  # Output time interval [s]

class BatchSimulator:

    def get_scenario_parameters(self):
        
        parser=ConfigParser()
        parser.read(Path.cwd() / 'configs' / 'base_config.txt')

        def parse_float_input(user_input : str, header: str, para : str) -> int :
            try:
                output = float(user_input)
                return output
            except Exception as e:
                return float(parser[header][para])

        print("Scenario Parameters:")
        print("Input that are non-parsable to be float will set parameters to base values.\n")
        
        d :float = parse_float_input(
            user_input=input("Water Depth (base = 1.0) [m]: "), 
            header="DOMAIN",
            para="d"
            )
        a : float = parse_float_input(
            user_input=input("Wave Amplitude (base = 0.3) [m]: "),
            header="WAVE",
            para="a"
            )
        omega : float = parse_float_input(
            user_input=input("Angular Frequency (base = 0.628) [rad/s]: "),
            header="WAVE",
            para="omega")
        start : float = parse_float_input(
            user_input=input("Vegetation Start (base = 100.0) [m]: "), 
            header="VEGETATION",
            para="start")
        end : float = parse_float_input(
            user_input=input("Vegetation End (base = 200.0) [m]: "), 
            header="VEGETATION",
            para="end")
        veg_density : str = input("Vegetation Density (base:average) <Input 0 for 'sparse', 2 for 'dense', anything else for base>: ")

        #Input Correction for vegetation width
        end = float(parser["DOMAIN"]["L"]) if end > float(parser["DOMAIN"]["L"]) else end
        start = end - 1 if start >= end else start
        
        if veg_density == "0":
            veg_density = "sparse"
        elif veg_density == "2":
            veg_density = "dense"
        else:
            veg_density = parser['VEGETATION']['density']
        
        self.scn_config = ScenarioConfig(
            L=float(parser['DOMAIN']['L']),
            d=d,
            dx=float(parser['DOMAIN']['dx']),
            T=float(parser['DOMAIN']['T']),
            A=a,
            omega=omega,
            veg_start=start,
            veg_end=end,
            veg_density=veg_density,
            cfl_target=float(parser['NUMERICAL']['cfl_target']),
            output_dt=float(parser['NUMERICAL']['output_dt'])
        )

    def _linearized_drag_coeff(
            self,
            m : MangroveConfig, 
            wave_amp : float, 
            water_depth : float, 
            density : str): 
        
        def get_value(rng: tuple[float]) -> float:
            match density:
                case "sparse": 
                    return rng[0]
                case "dense": 
                    return rng[1]
                case _: #average
                    return (rng[0] + rng[1]) / 2.0
        
        C_D = get_value(m.bulk_drag_c)
        N = get_value(m.r_density)
        d_s = get_value(m.r_diameter)
        h_v = get_value(m.r_height)

        u_0 = wave_amp * math.sqrt(9.8 / water_depth)
        return (4.0 / (3.0 * math.pi * water_depth)) * C_D * N * d_s * h_v * u_0

    def run_simulations(self) -> tuple[list[Path],Path]:
        """
        Runs a simulation on based on each mangrove species provided along with the 
        given scenario configuration.

        Returns a list of the output files and the output directory.
        """

        sp_config_dir = Path.cwd() / 'configs' / 'sp_configs'

        output_dir_base = Path.cwd() / 'outputs'
        log_dir_base = Path.cwd() / 'logs' 

        # Create directories if they don't exist
        output_dir_base.mkdir(exist_ok=True)
        log_dir_base.mkdir(exist_ok=True)

        base_set_dir = f"A-{self.scn_config.A}_d-{self.scn_config.d}_omega-{self.scn_config.omega}_start-{self.scn_config.veg_start}_end-{self.scn_config.veg_end}_density{self.scn_config.veg_density}"

        output_dir = output_dir_base / base_set_dir
        log_dir = log_dir_base / base_set_dir

        output_files : list[Path] = []

        for file_path in sp_config_dir.glob('*.txt'):
            if file_path.is_file():
                parser = ConfigParser()
                parser.read(file_path)

                mngr_config = MangroveConfig(
                    sp_name=file_path.stem,
                    bulk_drag_c=(
                        float(parser['BULK DRAG COEFFICIENT']['minimum']),
                        float(parser['BULK DRAG COEFFICIENT']['maximum'])
                        ),
                    r_density=(
                        float(parser['ROOT DENSITY']['minimum']),
                        float(parser['ROOT DENSITY']['maximum'])
                        ),
                    r_diameter=(
                        float(parser['ROOT DIAMETER']['minimum']),
                        float(parser['ROOT DIAMETER']['maximum'])
                        ),
                    r_height=(
                        float(parser['ROOT HEIGHT']['minimum']),
                        float(parser['ROOT HEIGHT']['maximum'])
                        )
                )
            else:
                continue

            # Generate output filenames WITHOUT timestamp
            base_name = f"{mngr_config.sp_name}"
            output_file = output_dir / f"{base_name}.nc"
            log_file = log_dir / f"{base_name}.log"

            # Setup logging
            logger = cli.setup_logging(log_file)

            logger.info("="*50)
            logger.info("Simple 1D Wave Attenuation Model")
            logger.info("="*50)
            logger.info(f"Version: {cli.__version__}")
            logger.info(f"Configuration: N/A")
            logger.info(f"Output file: {output_file}")
            logger.info(f"Log file: {log_file}")
            logger.info("")

            try:
                # Load configuration
                logger.info("Loading configuration...")
                config = s.Config(
                    # Domain parameters
                    L=self.scn_config.L,                   # Domain length [m]
                    d=self.scn_config.d,                   # Water depth [m]
                    dx=self.scn_config.dx,                 # Spatial discretization [m]
                    T=self.scn_config.T,                   # Total simulation time [s]
                    
                    # Wave parameters
                    A=self.scn_config.A,                   # Wave amplitude [m]
                    omega=self.scn_config.omega,           # Angular frequency [rad/s]
                    
                    # Vegetation parameters
                    veg_start=self.scn_config.veg_start,   # Vegetation zone start [m]
                    veg_end=self.scn_config.veg_end,       # Vegetation zone end [m]
                    cD=self._linearized_drag_coeff(         # Drag coefficient [1/s]
                        m=mngr_config,
                        wave_amp=self.scn_config.A,
                        water_depth=self.scn_config.d,
                        density=self.scn_config.veg_density
                    ),                
                    # Numerical parameters
                    cfl_target=self.scn_config.cfl_target, # Target CFL number (Courant-Friedrichs-Lewy)
                    output_dt=self.scn_config.output_dt    # Output time interval [s]
                )

                # Create and run solver
                solver = s.WaveSolver(config, logger)
                solver.solve()
                solver.calculate_transmission()

                # Save results
                solver.save_results(str(output_file))

                # Write summary to log
                cli.write_summary_log(log_file, config, solver)

                logger.info("") 
                logger.info("Simulation completed successfully!")
                logger.info(f"Results saved to: {output_file}")
                logger.info(f"Log saved to: {log_file}")

                output_files.append(output_file)
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
                sys.exit(1)

        return output_files, output_dir
    
    def run_controlled_simulations(
        self,
        variable: str,
        values: list[float | str],
        keep_width: bool = False
    ) -> tuple[list[Path], Path]:

        """
        Performs controlled OFAT simulations.

        Only one scenario variable changes.
        All other parameters remain at baseline values.

        Example:
            variable="d"
            values=[1.0,1.5,2.0,2.5]

        varies water depth only.

        Keep width parameter is when veg_end is the controlled variable,
        it make the vegetation width be same all throughout.
        """

        output_files = []

        output_dir_base = Path.cwd() / "outputs"
        log_dir_base = Path.cwd() / "logs"

        output_dir_base.mkdir(exist_ok=True)
        log_dir_base.mkdir(exist_ok=True)

        sp_config_dir = Path.cwd() / "configs" / "sp_configs"

        for test_value in values:

            # Copy baseline config
            scenario = ScenarioConfig(**vars(self.scn_config))

            if variable == "veg_end" and keep_width:
                new_veg_start = test_value-(scenario.veg_end-scenario.veg_start) if test_value-(scenario.veg_end-scenario.veg_start) > 0 else 0
                setattr(scenario, "veg_start", new_veg_start)
            
            # Override ONE parameter
            setattr(scenario, variable, test_value)

            batch_name = f"controlled_{variable}-{test_value}"

            output_dir = output_dir_base / batch_name
            log_dir = log_dir_base / batch_name

            output_dir.mkdir(exist_ok=True)
            log_dir.mkdir(exist_ok=True)

            for file_path in sp_config_dir.glob("*.txt"):

                parser = ConfigParser()
                parser.read(file_path)

                mngr_config = MangroveConfig(
                    sp_name=file_path.stem,

                    bulk_drag_c=(
                        float(parser['BULK DRAG COEFFICIENT']['minimum']),
                        float(parser['BULK DRAG COEFFICIENT']['maximum'])
                    ),

                    r_density=(
                        float(parser['ROOT DENSITY']['minimum']),
                        float(parser['ROOT DENSITY']['maximum'])
                    ),

                    r_diameter=(
                        float(parser['ROOT DIAMETER']['minimum']),
                        float(parser['ROOT DIAMETER']['maximum'])
                    ),

                    r_height=(
                        float(parser['ROOT HEIGHT']['minimum']),
                        float(parser['ROOT HEIGHT']['maximum'])
                    )
                )

                output_file = output_dir / f"{mngr_config.sp_name}.nc"
                log_file = log_dir / f"{mngr_config.sp_name}.log"

                logger = cli.setup_logging(log_file)

                try:

                    config = s.Config(

                        L=scenario.L,
                        d=scenario.d,
                        dx=scenario.dx,
                        T=scenario.T,

                        A=scenario.A,
                        omega=scenario.omega,

                        veg_start=scenario.veg_start,
                        veg_end=scenario.veg_end,

                        cD=self._linearized_drag_coeff(
                            m=mngr_config,
                            wave_amp=scenario.A,
                            water_depth=scenario.d,
                            density=scenario.veg_density
                        ),

                        cfl_target=scenario.cfl_target,
                        output_dt=scenario.output_dt
                    )

                    solver = s.WaveSolver(config, logger)

                    solver.solve()
                    solver.calculate_transmission()

                    solver.save_results(str(output_file))

                    output_files.append(output_file)

                except Exception as e:
                    logger.error(f"Error: {e}", exc_info=True)
                    continue

        return output_files, output_dir_base