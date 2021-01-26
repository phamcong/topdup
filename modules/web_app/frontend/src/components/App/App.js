import "./App.scss";
import React from "react";
import { BrowserRouter, Route, Switch } from "react-router-dom";
import Dashboard from "../Dashboard/Dashboard";
import Preferences from "../Preferences/Preferences";
import Login from "../Login/Login";
import useToken from "./useToken";
import NavigationBar from "../../shared/components/navigation-bar/navigation-bar";
import SimilarityReport from "../Similarity-Report/Similarity-Report";

function App() {
	const { token, setToken } = useToken();

	return (
		<BrowserRouter>
			<div className="App">
				<NavigationBar isLoggedIn={token ? true : false} />

				<div className="page-content-wrapper">
					<Switch>
						<Route
							exact
							path="/"
							component={() => {
								return !token ? <Login setToken={setToken} /> : <Dashboard />;
							}}
						/>
						<Route exact path="/dashboard" component={Dashboard} />
						<Route exact path="/preferences" component={Preferences} />
						<Route exact path="/similarity-report" component={SimilarityReport} />
					</Switch>
				</div>
			</div>
		</BrowserRouter>
	);
}

export default App;
