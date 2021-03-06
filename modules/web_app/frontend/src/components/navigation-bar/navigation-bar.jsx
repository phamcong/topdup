import React from "react"
import { Container, Nav, Navbar } from "react-bootstrap"
import { useLocation } from "react-router-dom"
import Authentication from "../auth/auth"
import logo from "./../../images/logo.svg"
import "./navigation-bar.css"

const NavigationBar = (props) => {
  const location = useLocation()
  const logOut = () => {
    props.setUserData()
    window.location.assign("/")
  }

  return (
    <>
      <Navbar expand="lg" fixed="top">
        <Container>
          <Navbar.Brand className="topdup-brand" href="/">
            <img src={logo} style={{ width: "120px" }} alt="" />
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav className="mr-auto" activeKey={location.pathname}></Nav>
            <Nav className="topdup-nav-items">
              <div>
                <Nav.Link href="/about">Giới thiệu</Nav.Link>
              </div>
              <div>
                <Nav.Link href="/dup-report">DupReport</Nav.Link>
              </div>
              <div>
                <Nav.Link href="/dup-compare">DupCompare</Nav.Link>
              </div>
              <Authentication setUserData={props.setUserData} />
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>
    </>
  )
}

export default NavigationBar
