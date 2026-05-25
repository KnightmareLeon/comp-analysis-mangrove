from simulation import get_scenario_parameters, run_simulations
from comparison import Comparator
if __name__ == "__main__":

    scn_params = get_scenario_parameters()
    
    output_files, output_dir = run_simulations(scr_config=scn_params)

    comparator = Comparator(
        sim_files=output_files,
        output_dir=output_dir
    )

    comparator.print_comparison()
    comparator.save_comparison_csv()
    comparator.plot_wave_reduction()
    comparator.plot_drag_coeffs()
    comparator.plot_transmission_coeff()
    comparator.plot_energy_loss()