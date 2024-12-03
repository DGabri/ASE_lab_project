import axios from 'axios'

const getBanners = async (access_token) => {
    console.log(access_token)
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const responses = []

    for (let i = 1; i <= 3; i++) {
        let response = await axiosInstance.get(
            `https://localhost:3000/banner/banner/${i}`,
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${access_token}`
                }
            }
        )
    
        if (response.status != 200) {
            throw new Error(response.data.err)  
        }

        responses.push(response)
    }
    
    return responses.map(response => response.data.banner)
}

export default getBanners