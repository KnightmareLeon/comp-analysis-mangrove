from simulation import get_scenario_parameters, run_simulations

if __name__ == "__main__":

    scn_params = get_scenario_parameters()
    
    output_files = run_simulations(scr_config=scn_params)

    