from simulation import BatchSimulator
from comparison import Comparator
if __name__ == "__main__":

    simulator = BatchSimulator()
    simulator.get_scenario_parameters()
    
    output_files, output_dir = simulator.run_simulations()

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

    controlled_output_files, controlled_output_dir = simulator.run_controlled_simulations(
        variable="veg_end",
        values=list(range(200, 105, -5)),
        keep_width=True
    )

    controlled_comparator = Comparator(
        sim_files=controlled_output_files,
        output_dir=controlled_output_dir
    )

    controlled_comparator.plot_controlled_line(
        x_variable="vegetation_cross_shore_distance",
        y_variable="wave_reduction"
    )

    controlled_comparator.plot_controlled_line(
        x_variable="vegetation_cross_shore_distance",
        y_variable="energy_loss"
    )
