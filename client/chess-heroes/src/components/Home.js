import { Link } from 'react-router-dom'
import Container from 'react-bootstrap/Container'
import Button from 'react-bootstrap/Button'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import homeChessPiece from '../assets/home-chess-piece.svg'
import pack from '../assets/pack.svg'
import auction from '../assets/auction.svg'

const Home = () => {
    return <Container fluid className="d-flex gap-5 flex-column p-0">
        <Container fluid className="d-flex justify-content-center align-items-center flex-column gap-4 bg-dark" style={{padding: "100px"}}>
            <Row>
                <h1 className="text-white text-center">Chess Heroes</h1>
            </Row>
            <Row style={{maxWidth: "600px"}}>
                <h4 className="text-body text-center">A simple gacha game where you can collect chess pieces, buy packs of pieces, and participate in auctions to have the possibility of winning pieces.</h4>
            </Row>
            <Row>
                <Col>
                    <Link to="/login" className="text-decoration-none">
                        <Button variant="primary">Login</Button>
                    </Link>
                </Col>
                <Col>
                <Link to="/register" className="text-decoration-none">
                        <Button variant="primary">Register</Button>
                    </Link>
                </Col>
            </Row>
        </Container>
        <Container fluid className="d-flex justify-content-center align-items-center bg-dark" style={{padding: "100px", gap: "100px"}}>
            <Col className="d-flex flex-column gap-4" style={{maxWidth: "450px"}}>
                <Row>
                    <h1 className="text-white">Buy packets</h1>
                </Row>
                <Row>
                    <h4 className="text-body">You have the possibility to buy packets containing random pieces to add to your collection.</h4>
                </Row>
            </Col>
            <Col className="d-flex justify-content-center align-items-center flex-column" style={{maxWidth: "450px"}}>
                <img width="120" className="bounce2" src={homeChessPiece} />
                <img width="300" src={pack} />
            </Col>
        </Container>
        <Container fluid className="d-flex justify-content-center align-items-center bg-dark" style={{padding: "100px", gap: "100px"}}>
            <img width="300" src={auction} />
            <Col className="d-flex flex-column gap-4" style={{maxWidth: "450px"}}>
                <Row>
                    <h1 className="text-white">Auctions!</h1>
                </Row>
                <Row>
                    <h4 className="text-body">
                        In case you cannot find a particular piece, you can always participate in an auction.
                        Or if you have a few pieces left over, you can create an auction to sell that piece.
                    </h4>
                </Row>
            </Col>
        </Container>
    </Container>
}

export default Home